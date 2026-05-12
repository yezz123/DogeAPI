"use client";

import { ErrorState } from "@/components/page-state";

export default function Error({
  error,
}: {
  error: Error & { digest?: string };
}) {
  return (
    <ErrorState
      title="AI Template hit an unexpected state"
      message={error.message || "Refresh the page and try again."}
      actionHref="/dashboard"
      actionLabel="Go to dashboard"
    />
  );
}
