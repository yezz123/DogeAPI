import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function readPublicFlag(name: string): boolean {
  const value = process.env[`NEXT_PUBLIC_${name}`];
  return value === "true" || value === "1";
}
