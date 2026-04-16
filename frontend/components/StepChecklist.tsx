"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, Circle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface StepChecklistProps {
  githubUsername: string;
  repoFullName: string;
  issueId: number;
}

export default function StepChecklist({ githubUsername, repoFullName, issueId }: StepChecklistProps) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const saved = localStorage.getItem(`checklist-${issueId}`);
    if (saved) {
      setChecked(JSON.parse(saved));
    }
  }, [issueId]);

  const toggleCheck = (idx: number) => {
    const newChecked = { ...checked, [idx]: !checked[idx] };
    setChecked(newChecked);
    localStorage.setItem(`checklist-${issueId}`, JSON.stringify(newChecked));
  };

  const regex = /([^/]+)\/(.+)/;
  const match = repoFullName.match(regex);
  const repoName = match ? match[2] : repoFullName;

  const steps = [
    { title: "Fork the repo", cmd: "Click 'Fork' on the GitHub repository page." },
    { title: "Clone your fork", cmd: `git clone https://github.com/${githubUsername}/${repoName}.git` },
    { title: "Read CONTRIBUTING.md", cmd: `cd ${repoName} && cat CONTRIBUTING.md` },
    { title: "Create a branch", cmd: `git checkout -b fix-issue-${issueId}` },
    { title: "Make your changes", cmd: "Open your favorite editor and start coding!" },
    { title: "Commit and push", cmd: `git add .\ngit commit -m "Fix issue #${issueId}"\ngit push origin fix-issue-${issueId}` },
    { title: "Open a Pull Request", cmd: "Go to the original repository and click 'Compare & pull request'." },
  ];

  return (
    <div className="space-y-4">
      {steps.map((step, idx) => {
        const isChecked = !!checked[idx];
        return (
          <Card 
            key={idx} 
            className={`cursor-pointer transition-colors ${isChecked ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800' : 'hover:border-primary/50'}`}
            onClick={() => toggleCheck(idx)}
          >
            <CardContent className="p-4 flex gap-4 items-start">
              <div className="mt-0.5 shrink-0">
                {isChecked ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <Circle className="w-5 h-5 text-muted-foreground" />
                )}
              </div>
              <div className="space-y-1 w-full overflow-hidden">
                <h4 className={`font-semibold ${isChecked ? 'text-green-700 dark:text-green-400 line-through opacity-70' : ''}`}>
                  {idx + 1}. {step.title}
                </h4>
                <div className={`p-2 rounded bg-muted font-mono text-xs text-muted-foreground whitespace-pre-wrap break-all ${isChecked ? 'opacity-50' : ''}`}>
                  {step.cmd}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
