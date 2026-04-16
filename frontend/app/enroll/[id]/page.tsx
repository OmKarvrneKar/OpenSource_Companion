"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Issue, User } from "@/types";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import StepChecklist from "@/components/StepChecklist";
import DifficultyBadge from "@/components/DifficultyBadge";
import { ArrowLeft, ExternalLink } from "lucide-react";

export default function EnrollPage() {
  const { id } = useParams();
  const router = useRouter();
  
  const [issue, setIssue] = useState<Issue | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [issueRes, userRes] = await Promise.all([
          api.get(`/issues/${id}`),
          api.get("/users/me")
        ]);
        setIssue(issueRes.data);
        setUser(userRes.data);
      } catch (err) {
        console.error("Failed to load data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-4 space-y-6 mt-8">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-6 w-1/4" />
        <div className="space-y-4 py-8">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!issue || !user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <p className="text-xl text-muted-foreground">Issue not found or failed to load.</p>
        <Button onClick={() => router.push("/feed")}>Back to Feed</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <Button variant="ghost" className="mb-4 -ml-4" onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          
          <div className="bg-background p-6 rounded-xl border shadow-sm space-y-4">
            <div className="flex flex-wrap gap-2 mb-2">
              <DifficultyBadge difficulty={issue.difficulty || "beginner"} />
              {issue.language && <span className="text-sm font-semibold text-muted-foreground px-2 py-0.5 bg-muted rounded">{issue.language}</span>}
              <span className="text-sm text-primary font-semibold ml-auto">{issue.repo_name}</span>
            </div>
            
            <h1 className="text-2xl md:text-3xl font-bold">{issue.title}</h1>
            
            <div className="flex gap-4 pt-2">
              <Button asChild>
                <a href={issue.github_url || "#"} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Original Issue
                </a>
              </Button>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-xl font-bold mb-4">Contribution Guide</h2>
          <p className="text-muted-foreground mb-6">
            Follow this checklist to complete your contribution. Your progress is saved automatically.
          </p>
          
          <StepChecklist 
            githubUsername={user.github_username} 
            repoFullName={issue.repo_name || "owner/repo"} 
            issueId={issue.id} 
          />
        </div>
      </div>
    </div>
  );
}
