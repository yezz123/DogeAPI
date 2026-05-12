import { readPublicFlag } from "@/lib/utils";

export const frontendFeatures = {
  apiKeys: readPublicFlag("FEATURE_API_KEYS"),
  auditLog: readPublicFlag("FEATURE_AUDIT_LOG"),
  aiChat: readPublicFlag("FEATURE_AI_CHAT"),
  stripe: readPublicFlag("FEATURE_STRIPE"),
};
