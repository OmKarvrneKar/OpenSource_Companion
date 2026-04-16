"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Issue } from "@/types";
import api from "@/lib/api";
import IssueCard from "@/components/IssueCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function FeedPage() {
  const router = useRouter();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [enrollingId, setEnrollingId] = useState<number | null>(null);
  
  const [diffFilter, setDiffFilter] = useState("all");
  const [langFilter, setLangFilter] = useState("all");

  const [availableLangs, setAvailableLangs] = useState<string[]>([]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.get("/recommendations");
      const data: Issue[] = res.data;
      setIssues(data);
      
      const langs = Array.from(new Set(data.map(i => i.language).filter(Boolean))) as string[];
      setAvailableLangs(langs);
    } catch (err) {
      console.error("Failed to load recommendations", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleEnroll = async (issueId: number) => {
    setEnrollingId(issueId);
    try {
      await api.post("/enroll", { issue_id: issueId });
      router.push(`/enroll/${issueId}`);
    } catch (err) {
      console.error("Enrollment failed", err);
      alert("Failed to enroll in the issue.");
      setEnrollingId(null);
    }
  };

  const filteredIssues = issues.filter((issue) => {
    if (diffFilter !== "all" && issue.difficulty?.toLowerCase() !== diffFilter) return false;
    if (langFilter !== "all" && issue.language !== langFilter) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Recommended Issues</h1>
            <p className="text-muted-foreground">Hand-picked open source opportunities for you.</p>
          </div>
          <Button variant="outline" onClick={fetchRecommendations} disabled={loading} className="gap-2">
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 bg-background p-4 rounded-lg shadow-sm border">
          <div className="flex-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">Difficulty</label>
            <Select value={diffFilter} onValueChange={setDiffFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Difficulties" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Difficulties</SelectItem>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase mb-1 block">Language</label>
            <Select value={langFilter} onValueChange={setLangFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Languages" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Languages</SelectItem>
                {availableLangs.map(lang => (
                  <SelectItem key={lang} value={lang}>{lang}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex flex-col space-y-3">
                <Skeleton className="h-[200px] w-full rounded-xl" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredIssues.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredIssues.map((issue) => (
              <IssueCard 
                key={issue.id} 
                issue={issue} 
                onEnroll={handleEnroll} 
                enrolling={enrollingId === issue.id}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 text-muted-foreground bg-background rounded-lg border">
            <p>No issues match your current filters.</p>
            <Button variant="link" onClick={() => { setDiffFilter("all"); setLangFilter("all"); }}>
              Clear filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
