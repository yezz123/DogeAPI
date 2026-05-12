import { ErrorState } from "@/components/page-state";

export default function NotFound() {
  return (
    <ErrorState
      title="Page not found"
      message="That AI Template screen is not part of this boilerplate."
      actionHref="/dashboard"
      actionLabel="Go to dashboard"
    />
  );
}
