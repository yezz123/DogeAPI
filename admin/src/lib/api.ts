/**
 * Same BFF + CSRF pattern as the tenant frontend.
 *
 * authx issues a `csrf_access_token` cookie at login and requires it back
 * as the `X-CSRF-TOKEN` header on cookie-authenticated mutations. We read
 * the cookie client-side and attach it automatically.
 */

const BFF_PREFIX = "/api/backend";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export type ApiError = {
  status: number;
  detail: string;
};

function readCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : undefined;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const { json, headers, ...rest } = init ?? {};
  const method = (rest.method ?? "GET").toUpperCase();

  const csrfHeaders: Record<string, string> = {};
  if (MUTATING_METHODS.has(method)) {
    const cookieName = path.startsWith("/auth/refresh")
      ? "csrf_refresh_token"
      : "csrf_access_token";
    const token = readCookie(cookieName);
    if (token) csrfHeaders["X-CSRF-TOKEN"] = token;
  }

  const response = await fetch(`${BFF_PREFIX}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...csrfHeaders,
      ...(headers ?? {}),
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body?.detail ?? body?.msg ?? detail;
    } catch {
      // body wasn't JSON; keep statusText
    }
    const err: ApiError = { status: response.status, detail };
    throw err;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
