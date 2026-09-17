"use client";

import { useEffect, useState } from "react";

import { DocumentListItem } from "@/components/admin/DocumentListItem";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export default function AdminDocumentsPage() {
  const { token } = useAuth();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    api
      .listDocuments(token)
      .then(setDocs)
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-text-dim">
        Source documents currently grounding the assistant&apos;s answers.
      </p>
      {loading ? (
        <p className="font-body text-md text-text-dim">Loading documents...</p>
      ) : (
        <div className="flex flex-col gap-3">
          {docs.map((doc) => (
            <DocumentListItem key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
