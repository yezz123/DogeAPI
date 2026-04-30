import { apiFetch } from "@/lib/api";

export type AgentDescriptor = {
  id: string;
  name: string;
  description: string;
  input_label: string;
  output_kind: "json" | "text";
};

export type AgentsList = {
  agents: AgentDescriptor[];
};

export type ExtractedTask = {
  title: string;
  description: string | null;
  due_iso: string | null;
  priority: "low" | "medium" | "high";
};

export type TaskExtractorResult = {
  task: ExtractedTask;
  tokens_in: number;
  tokens_out: number;
};

export type ConciergeResult = {
  text: string;
  model: string | null;
};

export const listAgents = (slug: string) =>
  apiFetch<AgentsList>(`/orgs/${slug}/ai/agents`);

export const runTaskExtractor = (slug: string, text: string) =>
  apiFetch<TaskExtractorResult>(`/orgs/${slug}/ai/agents/task-extractor`, {
    method: "POST",
    json: { text },
  });

export const runConcierge = (slug: string, text: string) =>
  apiFetch<ConciergeResult>(`/orgs/${slug}/ai/agents/concierge`, {
    method: "POST",
    json: { text },
  });
