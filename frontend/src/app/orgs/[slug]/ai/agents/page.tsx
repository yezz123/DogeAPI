"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  listAgents,
  runConcierge,
  runTaskExtractor,
  type AgentDescriptor,
  type ConciergeResult,
  type ExtractedTask,
  type TaskExtractorResult,
} from "@/lib/agents";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { readPublicFlag, cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

type AgentRunState = {
  loading: boolean;
  error: string | null;
  result: TaskExtractorResult | ConciergeResult | null;
};

const initialRunState: AgentRunState = {
  loading: false,
  error: null,
  result: null,
};

const PRIORITY_TONE: Record<ExtractedTask["priority"], string> = {
  high: "bg-destructive text-destructive-foreground",
  medium: "border border-border bg-muted",
  low: "border border-border bg-muted text-muted-foreground",
};

export default function AIAgentsPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const aiEnabled = readPublicFlag("FEATURE_AI_CHAT");
  const [agents, setAgents] = useState<AgentDescriptor[] | null>(null);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const [state, setState] = useState<Record<string, AgentRunState>>({});
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!slug || !aiEnabled) return;
    listAgents(slug)
      .then((response) => setAgents(response.agents))
      .catch((err: ApiError) => {
        setDiscoveryError(err.detail ?? "Could not load agents");
      });
  }, [slug, aiEnabled]);

  function setAgentState(id: string, patch: Partial<AgentRunState>) {
    setState((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? initialRunState), ...patch },
    }));
  }

  async function handleRun(agent: AgentDescriptor) {
    const text = drafts[agent.id]?.trim() ?? "";
    if (!text) return;
    setAgentState(agent.id, { loading: true, error: null });
    try {
      let result: TaskExtractorResult | ConciergeResult;
      if (agent.id === "task-extractor") {
        result = await runTaskExtractor(slug, text);
      } else if (agent.id === "concierge") {
        result = await runConcierge(slug, text);
      } else {
        throw new Error(`Unknown agent ${agent.id}`);
      }
      setAgentState(agent.id, { loading: false, error: null, result });
    } catch (err) {
      const apiErr = err as ApiError;
      setAgentState(agent.id, {
        loading: false,
        error: apiErr.detail ?? "Run failed",
        result: null,
      });
    }
  }

  if (!aiEnabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Agents</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          AI is disabled in this environment.
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <header className="space-y-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href={`/orgs/${slug}/ai`} className="hover:underline">
            ← Back to chat
          </Link>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Pydantic AI agents
        </h1>
        <p className="text-sm text-muted-foreground">
          Typed agents built on top of the LLM Gateway. The examples below live
          in{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            backend/src/dogeapi/ai/examples.py
          </code>
          {" — "}copy them as a starting point for your own.
        </p>
      </header>

      {discoveryError && (
        <p className="text-sm text-destructive">{discoveryError}</p>
      )}

      {agents === null && !discoveryError && (
        <p className="text-sm text-muted-foreground">Loading agents…</p>
      )}

      {agents && (
        <div className="grid gap-4 lg:grid-cols-2">
          {agents.map((agent) => {
            const runState = state[agent.id] ?? initialRunState;
            const draft = drafts[agent.id] ?? "";
            return (
              <Card key={agent.id} className="flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{agent.name}</span>
                    <span
                      className={cn(
                        "rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground",
                      )}
                    >
                      {agent.output_kind === "json" ? "structured" : "text"}
                    </span>
                  </CardTitle>
                  <CardDescription>{agent.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-4">
                  <Field>
                    <Label htmlFor={`agent-input-${agent.id}`}>
                      {agent.input_label}
                    </Label>
                    <textarea
                      id={`agent-input-${agent.id}`}
                      value={draft}
                      onChange={(e) =>
                        setDrafts((prev) => ({
                          ...prev,
                          [agent.id]: e.target.value,
                        }))
                      }
                      rows={4}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    />
                    <FieldError>{runState.error}</FieldError>
                  </Field>

                  <div className="flex items-center justify-between">
                    <Button
                      onClick={() => handleRun(agent)}
                      disabled={runState.loading || !draft.trim()}
                      size="sm"
                    >
                      {runState.loading ? "Running…" : "Run agent"}
                    </Button>
                    {runState.result && "tokens_in" in runState.result && (
                      <span className="font-mono text-xs text-muted-foreground">
                        {runState.result.tokens_in}+{runState.result.tokens_out}
                        t
                      </span>
                    )}
                  </div>

                  <AnimatePresence mode="wait">
                    {runState.result && (
                      <motion.div
                        key={JSON.stringify(runState.result)}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="rounded-md border border-border bg-muted/40 p-3 text-sm"
                      >
                        {agent.id === "task-extractor"
                          ? renderExtractedTask(
                              (runState.result as TaskExtractorResult).task,
                            )
                          : renderConciergeResult(
                              runState.result as ConciergeResult,
                            )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </motion.section>
  );
}

function renderExtractedTask(task: ExtractedTask) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="font-medium">{task.title}</p>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider",
            PRIORITY_TONE[task.priority],
          )}
        >
          {task.priority}
        </span>
      </div>
      {task.description && (
        <p className="text-sm text-muted-foreground">{task.description}</p>
      )}
      {task.due_iso && (
        <p className="font-mono text-xs text-muted-foreground">
          due {task.due_iso}
        </p>
      )}
      <details className="group text-xs">
        <summary className="cursor-pointer text-muted-foreground group-open:text-foreground">
          Raw JSON
        </summary>
        <pre className="mt-2 overflow-x-auto rounded-md bg-background p-2 font-mono text-[11px]">
          {JSON.stringify(task, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function renderConciergeResult(result: ConciergeResult) {
  return (
    <div className="space-y-2">
      <p className="whitespace-pre-wrap">{result.text}</p>
      {result.model && (
        <p className="font-mono text-[10px] text-muted-foreground">
          {result.model}
        </p>
      )}
    </div>
  );
}
