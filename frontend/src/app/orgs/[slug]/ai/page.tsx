"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  createThread,
  deleteThread,
  getThread,
  listModels,
  listThreads,
  sendMessage,
  type Message,
  type ModelInfo,
  type ModelsList,
  type Thread,
} from "@/lib/ai";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { readPublicFlag, cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

function formatCost(value: string | number | undefined): string {
  if (value === undefined) return "$0";
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n) || n === 0) return "$0";
  if (n < 0.0001) return `$${(n * 1_000_000).toFixed(2)}µ`;
  if (n < 0.01) return `$${(n * 1000).toFixed(3)}m`;
  return `$${n.toFixed(4)}`;
}

export default function AIChatPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const aiEnabled = readPublicFlag("FEATURE_AI_CHAT");
  const [models, setModels] = useState<ModelsList | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [usage, setUsage] = useState<{
    used: number;
    limit: number | null;
  } | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const groupedModels = useMemo(() => {
    const out: Record<string, ModelInfo[]> = {};
    for (const m of models?.models ?? []) {
      (out[m.family] ??= []).push(m);
    }
    return out;
  }, [models]);

  async function reloadModels() {
    if (!aiEnabled) return;
    try {
      const result = await listModels(slug);
      setModels(result);
      setSelectedModel((prev) => prev || result.default_model);
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load models");
    }
  }

  async function reloadThreads() {
    if (!aiEnabled) return;
    try {
      setThreads(await listThreads(slug));
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load threads");
    }
  }

  async function loadThread(id: string) {
    setActiveId(id);
    try {
      const detail = await getThread(slug, id);
      setMessages(detail.messages);
      if (detail.thread.default_model) {
        setSelectedModel(detail.thread.default_model);
      }
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load thread");
    }
  }

  useEffect(() => {
    reloadModels();
    reloadThreads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function handleNewThread() {
    try {
      const thread = await createThread(slug, {
        default_model: selectedModel || undefined,
      });
      await reloadThreads();
      setActiveId(thread.id);
      setMessages([]);
    } catch (err) {
      setError((err as ApiError).detail ?? "Could not create thread");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await deleteThread(slug, id);
      await reloadThreads();
      if (id === activeId) {
        setActiveId(null);
        setMessages([]);
      }
    } catch (err) {
      setError((err as ApiError).detail ?? "Could not delete");
    }
  }

  async function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.trim() || !activeId) return;
    const content = input;
    setInput("");
    setBusy(true);
    try {
      const result = await sendMessage(
        slug,
        activeId,
        content,
        selectedModel || undefined,
      );
      setMessages((prev) => [
        ...prev,
        result.user_message,
        result.assistant_message,
      ]);
      setUsage({
        used: result.monthly_tokens_used,
        limit: result.monthly_token_limit,
      });
    } catch (err) {
      setError((err as ApiError).detail ?? "Send failed");
    } finally {
      setBusy(false);
    }
  }

  if (!aiEnabled) {
    return (
      <Card>
        <CardContent className="text-sm text-muted-foreground">
          AI chat is disabled in this environment.
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="grid h-[calc(100vh-12rem)] grid-cols-[260px,1fr] gap-4"
    >
      <aside className="overflow-y-auto rounded-md border border-border">
        <div className="flex items-center justify-between border-b border-border p-3">
          <h2 className="text-sm font-medium">Conversations</h2>
          <Button size="sm" onClick={handleNewThread}>
            +
          </Button>
        </div>
        <ul className="divide-y divide-border">
          {threads.map((t) => (
            <li
              key={t.id}
              className={cn(
                "flex items-center justify-between gap-2 px-3 py-2 text-sm",
                activeId === t.id ? "bg-muted" : "hover:bg-muted/60",
              )}
            >
              <button
                onClick={() => loadThread(t.id)}
                className="flex-1 truncate text-left"
              >
                <span>{t.title}</span>
                {t.default_model && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {t.default_model}
                  </span>
                )}
              </button>
              <button
                onClick={() => handleDelete(t.id)}
                className="text-xs text-muted-foreground hover:text-destructive"
                aria-label="Delete"
              >
                ×
              </button>
            </li>
          ))}
          {threads.length === 0 && (
            <li className="px-3 py-4 text-xs text-muted-foreground">
              No conversations yet.
            </li>
          )}
        </ul>
      </aside>

      <div className="flex min-h-0 flex-col rounded-md border border-border">
        <div className="flex items-center justify-between border-b border-border px-4 py-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Model</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="h-8 rounded-md border border-border bg-background px-2"
            >
              {models === null ? (
                <option>Loading…</option>
              ) : Object.keys(groupedModels).length === 0 ? (
                <option value={models.default_model}>
                  {models.default_model}
                </option>
              ) : (
                Object.entries(groupedModels).map(([family, list]) => (
                  <optgroup key={family} label={family}>
                    {list.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                        {m.free ? " · free" : ""}
                      </option>
                    ))}
                  </optgroup>
                ))
              )}
            </select>
            {models && !models.configured && (
              <span className="rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                offline echo
              </span>
            )}
          </div>
          {usage && (
            <span className="text-muted-foreground">
              {usage.used.toLocaleString()} /{" "}
              {usage.limit ? usage.limit.toLocaleString() : "∞"} tokens this
              month
            </span>
          )}
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {error && <p className="text-sm text-destructive">{error}</p>}
          {messages.length === 0 && activeId === null && (
            <p className="text-sm text-muted-foreground">
              Pick a conversation or create a new one.
            </p>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                "rounded-md p-3 text-sm",
                m.role === "user"
                  ? "ml-12 bg-primary text-primary-foreground"
                  : "mr-12 bg-muted",
              )}
            >
              <p className="mb-1 flex items-center justify-between text-xs opacity-70">
                <span>{m.role}</span>
                {m.role === "assistant" && (
                  <span className="font-mono">
                    {m.model} · {m.tokens_in}+{m.tokens_out}t ·{" "}
                    {formatCost(m.cost_usd)}
                  </span>
                )}
              </p>
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        {activeId && (
          <form
            onSubmit={handleSend}
            className="flex gap-2 border-t border-border p-3"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message…"
              disabled={busy}
            />
            <Button type="submit" disabled={busy || !input.trim()}>
              {busy ? "…" : "Send"}
            </Button>
          </form>
        )}
      </div>
    </motion.section>
  );
}
