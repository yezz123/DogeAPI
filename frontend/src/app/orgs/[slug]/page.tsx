"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { listMembers, type Member } from "@/lib/orgs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FeatureBadge, PageHeader } from "@/components/page-state";
import { useOrgContext } from "@/lib/org-context";

export default function OrgOverviewPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { org } = useOrgContext();
  const [members, setMembers] = useState<Member[] | null>(null);

  useEffect(() => {
    if (!slug) return;
    listMembers(slug)
      .then(setMembers)
      .catch(() => setMembers([]));
  }, [slug]);

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <PageHeader
        eyebrow="Workspace overview"
        title={org?.name ?? "Overview"}
        description="A compact view of the tenant boundary: people, plan, and operational status."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Members</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold tracking-tight">
              {members?.length ?? "-"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <FeatureBadge tone="accent">{org?.plan ?? "Free"}</FeatureBadge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <FeatureBadge tone="success">Active</FeatureBadge>
          </CardContent>
        </Card>
      </div>
    </motion.section>
  );
}
