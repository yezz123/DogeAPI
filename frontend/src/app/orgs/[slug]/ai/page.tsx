"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  createThread,
  deleteThread,
  getThread,
  listThreads,
  sendMessage,
  type Message,
  type Thread,
} from "@/lib/ai";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { readPublicFlag, cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

export default function AIChatPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const aiEnabled = readPublicFlag("FEATURE_AI_CHAT");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

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
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load thread");
    }
  }

  useEffect(() => {
    reloadThreads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function handleNewThread() {
    try {
      const thread = await createThread(slug);
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
      const result = await sendMessage(slug, activeId, content);
      setMessages((prev) => [
        ...prev,
        result.user_message,
        result.assistant_message,
      ]);
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
                {t.title}
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
              <p className="mb-1 text-xs opacity-70">{m.role}</p>
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
