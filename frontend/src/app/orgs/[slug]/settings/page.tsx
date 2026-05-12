"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FeatureBadge, PageHeader } from "@/components/page-state";
import { frontendFeatures } from "@/lib/features";

export default function SettingsPage() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <PageHeader
        eyebrow="Workspace controls"
        title="Settings"
        description="Review enabled modules and the control surfaces this boilerplate exposes for a tenant."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <SettingCard label="API keys" enabled={frontendFeatures.apiKeys} />
        <SettingCard label="Audit log" enabled={frontendFeatures.auditLog} />
        <SettingCard label="Billing" enabled={frontendFeatures.stripe} />
        <SettingCard label="AI workspace" enabled={frontendFeatures.aiChat} />
      </div>
    </motion.section>
  );
}

function SettingCard({ label, enabled }: { label: string; enabled: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{label}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {enabled
            ? "Visible in workspace navigation"
            : "Hidden by feature flag"}
        </span>
        <FeatureBadge tone={enabled ? "success" : "neutral"}>
          {enabled ? "On" : "Off"}
        </FeatureBadge>
      </CardContent>
    </Card>
  );
}
