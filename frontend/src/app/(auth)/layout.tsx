import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            AI Template
          </Link>
          <nav className="flex gap-2 text-sm">
            <Link href="/login" className="px-3 py-1.5 hover:underline">
              Sign in
            </Link>
            <Link href="/register" className="px-3 py-1.5 hover:underline">
              Sign up
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 items-center justify-center px-6 py-12">
        {children}
      </main>
    </div>
  );
}
