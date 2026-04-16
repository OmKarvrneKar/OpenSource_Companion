"use client";

import { Issue } from "@/types";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Clock, MessageSquare, Code2 } from "lucide-react";
import DifficultyBadge from "./DifficultyBadge";

interface IssueCardProps {
  issue: Issue;
  onEnroll: (issueId: number) => void;
  enrolling?: boolean;
}

export default function IssueCard({ issue, onEnroll, enrolling = false }: IssueCardProps) {
  return (
    <Card className="flex flex-col h-full hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start gap-4">
          <div className="space-y-1 w-full">
            <CardDescription className="text-xs font-semibold text-primary truncate">
              {issue.repo_name || "Unknown Repo"}
            </CardDescription>
            <CardTitle className="text-lg leading-tight line-clamp-2">
              {issue.title}
            </CardTitle>
          </div>
          {issue.match_score !== undefined && (
            <Badge variant="outline" className="shrink-0 bg-primary/10 text-primary border-primary/20">
              {issue.match_score}% Match
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="pb-4 flex-grow space-y-4">
        <div className="flex flex-wrap gap-2">
          <DifficultyBadge difficulty={issue.difficulty || "beginner"} />
          {issue.language && (
            <Badge variant="secondary" className="flex gap-1 items-center">
              <Code2 className="w-3 h-3" />
              {issue.language}
            </Badge>
          )}
        </div>
        
        <div className="flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {issue.days_open} days open
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare className="w-3 h-3" />
            {issue.comment_count} comments
          </span>
        </div>
      </CardContent>
      
      <CardFooter className="pt-0 flex gap-2">
        <Button 
          variant="default" 
          className="w-full" 
          onClick={() => onEnroll(issue.id)}
          disabled={enrolling}
        >
          {enrolling ? "Enrolling..." : "Enroll"}
        </Button>
        <Button variant="outline" size="icon" asChild>
          <a href={issue.github_url || "#"} target="_blank" rel="noopener noreferrer" title="View on GitHub">
            <ExternalLink className="w-4 h-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}
