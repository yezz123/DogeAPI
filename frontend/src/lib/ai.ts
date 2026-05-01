import { apiFetch } from "@/lib/api";

export type Thread = {
  id: string;
  org_id: string;
  user_id: string;
  title: string;
  default_model: string | null;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  thread_id: string;
  role: string;
  content: string;
  tokens_in: number;
  tokens_out: number;
  model: string | null;
  cost_usd: string;
  extra: Record<string, unknown>;
  created_at: string;
};

export type ThreadDetail = {
  thread: Thread;
  messages: Message[];
};

export type SendResult = {
  user_message: Message;
  assistant_message: Message;
  monthly_tokens_used: number;
  monthly_token_limit: number | null;
};

export type ModelInfo = {
  id: string;
  name: string;
  family: string;
  description: string;
  context_length: number;
  input_modalities: string[];
  output_modalities: string[];
  json_output: boolean;
  structured_outputs: boolean;
  free: boolean;
  deprecated: boolean;
};

export type ModelsList = {
  configured: boolean;
  default_model: string;
  models: ModelInfo[];
};

export const listModels = (slug: string) =>
  apiFetch<ModelsList>(`/orgs/${slug}/ai/models`);

export const listThreads = (slug: string) =>
  apiFetch<Thread[]>(`/orgs/${slug}/ai/threads`);

export const createThread = (
  slug: string,
  input: { title?: string; default_model?: string } = {},
) =>
  apiFetch<Thread>(`/orgs/${slug}/ai/threads`, {
    method: "POST",
    json: input,
  });

export const getThread = (slug: string, threadId: string) =>
  apiFetch<ThreadDetail>(`/orgs/${slug}/ai/threads/${threadId}`);

export const deleteThread = (slug: string, threadId: string) =>
  apiFetch<void>(`/orgs/${slug}/ai/threads/${threadId}`, { method: "DELETE" });

export const sendMessage = (
  slug: string,
  threadId: string,
  content: string,
  model?: string,
) =>
  apiFetch<SendResult>(`/orgs/${slug}/ai/threads/${threadId}/messages`, {
    method: "POST",
    json: model ? { content, model } : { content },
  });
