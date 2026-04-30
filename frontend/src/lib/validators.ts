import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .max(128, "At most 128 characters"),
  full_name: z.string().max(255).optional(),
});
export type RegisterInput = z.infer<typeof registerSchema>;

export const verifyEmailSchema = z.object({
  token: z.string().min(1),
});

export const slugRegex = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;

export const createOrgSchema = z.object({
  name: z.string().min(1, "Required").max(255),
  slug: z
    .string()
    .min(2)
    .max(64)
    .regex(slugRegex, "Lowercase letters, digits, and dashes only")
    .optional()
    .or(z.literal("")),
});
export type CreateOrgInput = z.infer<typeof createOrgSchema>;

export const inviteSchema = z.object({
  email: z.string().email("Enter a valid email"),
  role: z.enum(["owner", "admin", "member"]),
});
export type InviteInput = z.infer<typeof inviteSchema>;
