"use client";

import { useEffect, useState } from "react";
import { Enrollment, Badge, User } from "@/types";
import api from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Trophy, Star, Activity, CheckCircle2, Clock } from "lucide-react";
import BadgeShelf from "@/components/BadgeShelf";
import Link from "next/link";

interface LeaderboardEntry {
  user_id: number;
  github_username: string;
  points: number;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [meRes, enrollRes, badgeRes, leadRes] = await Promise.all([
          api.get("/users/me"),
          api.get("/enrollments"),
          api.get("/users/me").then(res => api.get(`/users/${res.data.id}/badges`)),
          api.get("/leaderboard")
        ]);
        
        setUser(meRes.data);
        setEnrollments(enrollRes.data);
        setBadges(badgeRes.data);
        setLeaderboard(leadRes.data.all_time || []);
      } catch (err) {
        console.error("Dashboard data load failed", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  const handleWithdraw = async (enrollmentId: number) => {
    if (!confirm("Are you sure you want to withdraw from this issue?")) return;
    try {
      await api.post(`/enrollments/${enrollmentId}/withdraw`);
      setEnrollments(enrollments.map(e => e.id === enrollmentId ? { ...e, status: "dropped" } : e));
    } catch (err) {
      console.error("Withdrawal failed", err);
    }
  };

  const activeEnrollments = enrollments.filter(e => e.status === "enrolled");
  const completedEnrollments = enrollments.filter(e => e.status === "completed");

  if (loading) {
    return (
      <div className="p-8 space-y-8 max-w-6xl mx-auto">
        <Skeleton className="h-32 w-full rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-64 col-span-2 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header Summary */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2 bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Trophy className="w-6 h-6 text-yellow-500" />
                {user?.points_total || 0} Total Points
              </CardTitle>
              <CardDescription>@{user?.github_username} • {user?.skill_level} developer</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button asChild><Link href="/feed">Find New Issues</Link></Button>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <Activity className="w-4 h-4" /> Activity Stats
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Active</span>
                  <span className="font-bold">{activeEnrollments.length}</span>
                </div>
                <div className="flex justify-between items-center text-green-600 dark:text-green-500">
                  <span className="text-sm font-medium">Completed</span>
                  <span className="font-bold">{completedEnrollments.length}</span>
                </div>
                <div className="flex justify-between items-center text-muted-foreground">
                  <span className="text-sm font-medium">Badges</span>
                  <span className="font-bold">{badges.length}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Active Enrollments */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Clock className="w-5 h-5 text-blue-500" />
                <h2 className="text-xl font-bold">Active Quests</h2>
              </div>
              
              {activeEnrollments.length === 0 ? (
                <Card className="bg-muted/50 border-dashed">
                  <CardContent className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                    <p>No active quests right now.</p>
                    <Button variant="link" asChild className="mt-2"><Link href="/feed">Find something to build</Link></Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {activeEnrollments.map(enrollment => (
                    <Card key={enrollment.id} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Issue #{enrollment.issue_id}</CardTitle>
                        <CardDescription>Enrolled on {new Date(enrollment.enrolled_at).toLocaleDateString()}</CardDescription>
                      </CardHeader>
                      <CardContent className="flex justify-between items-center p-4 pt-0">
                        <Button asChild><Link href={`/enroll/${enrollment.issue_id}`}>Continue Guide</Link></Button>
                        <Button variant="ghost" className="text-red-500 hover:text-red-700 hover:bg-red-50" onClick={() => handleWithdraw(enrollment.id)}>Withdraw</Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>
            
            {/* Completed */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <h2 className="text-xl font-bold">Completed Pasts</h2>
              </div>
              <div className="space-y-4">
                {completedEnrollments.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Your completed PRs will appear here.</p>
                ) : (
                  completedEnrollments.map(enrollment => (
                    <Card key={enrollment.id} className="bg-background/50">
                      <CardContent className="p-4 flex justify-between items-center">
                        <div>
                          <p className="font-semibold text-sm">Issue #{enrollment.issue_id}</p>
                          <p className="text-xs text-muted-foreground">Completed {new Date(enrollment.completed_at || "").toLocaleDateString()}</p>
                        </div>
                        {enrollment.pr_url && (
                          <a href={enrollment.pr_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                            View PR
                          </a>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </section>
            
            {/* Badge Shelf */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Star className="w-5 h-5 text-yellow-500" />
                <h2 className="text-xl font-bold">Badge Shelf</h2>
              </div>
              <Card>
                <CardContent className="p-6">
                  <BadgeShelf earnedBadges={badges} allBadges={[]} />
                </CardContent>
              </Card>
            </section>

          </div>

          {/* Sidebar - Leaderboard */}
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">All-Time Leaderboard</CardTitle>
                <CardDescription>Top 10 contributors</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y">
                  {leaderboard.length === 0 ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">No data yet</div>
                  ) : leaderboard.map((entry, idx) => (
                    <div 
                      key={entry.user_id} 
                      className={`flex justify-between items-center p-3 px-6 ${entry.github_username === user?.github_username ? 'bg-primary/10 font-bold' : ''}`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-5 text-center font-semibold ${idx < 3 ? 'text-primary' : 'text-muted-foreground'}`}>{idx + 1}</span>
                        <span className="text-sm">{entry.github_username}</span>
                      </div>
                      <span className="text-sm font-semibold">{entry.points} pts</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      </div>
    </div>
  );
}
