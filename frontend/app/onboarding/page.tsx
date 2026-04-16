"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import api from "@/lib/api";
import { User, SkillLevel } from "@/types";

const LANGUAGES = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "Ruby"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [user, setUser] = useState<User | null>(null);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [skillLevel, setSkillLevel] = useState<SkillLevel>("beginner");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/users/me")
      .then((res) => {
        setUser(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        if (err.response?.status !== 401) {
          setLoading(false);
        }
      });
  }, []);

  const toggleLanguage = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      await api.put("/users/profile", {
        skill_level: skillLevel,
        primary_language: selectedLanguages.join(","),
      });
      router.push("/feed");
    } catch (err) {
      console.error("Failed to update profile", err);
      setLoading(false);
    }
  };

  const skipOnboarding = () => {
    setSkillLevel("beginner");
    setSelectedLanguages([]);
    handleComplete();
  };

  if (loading && !user) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <Skeleton className="h-8 w-1/2 mb-4" />
            <Skeleton className="h-4 w-full" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-lg shadow-lg">
        {step === 1 && (
          <>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Welcome aboard!</CardTitle>
              <CardDescription>Let&apos;s personalize your OpenSource Companion experience.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-6">
              {user?.avatar_url && (
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-primary">
                  <Image src={user.avatar_url} alt="GitHub Avatar" width={128} height={128} />
                </div>
              )}
              <h2 className="text-xl font-semibold">@{user?.github_username || "Developer"}</h2>
              <p className="text-center text-muted-foreground">
                We&apos;ve pulled your GitHub profile. Now, let&apos;s match you with the perfect issues.
              </p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="ghost" onClick={skipOnboarding}>Skip</Button>
              <Button onClick={() => setStep(2)}>Continue</Button>
            </CardFooter>
          </>
        )}

        {step === 2 && (
          <>
            <CardHeader>
              <CardTitle>Languages you know</CardTitle>
              <CardDescription>Select all the programming languages you want to contribute in.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {LANGUAGES.map((lang) => (
                <Button
                  key={lang}
                  variant={selectedLanguages.includes(lang) ? "default" : "outline"}
                  onClick={() => toggleLanguage(lang)}
                  className="rounded-full"
                >
                  {lang}
                </Button>
              ))}
            </CardContent>
            <CardFooter className="flex justify-between mt-4">
              <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
              <Button onClick={() => setStep(3)}>Next</Button>
            </CardFooter>
          </>
        )}

        {step === 3 && (
          <>
            <CardHeader>
              <CardTitle>Your Experience Level</CardTitle>
              <CardDescription>We&apos;ll provide recommendations tailored to your skill block.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {[
                { val: "beginner", title: "Beginner", desc: "I&apos;m learning to code or just started open source" },
                { val: "intermediate", title: "Intermediate", desc: "I&apos;ve merged a few PRs before" },
                { val: "advanced", title: "Advanced", desc: "I contribute to OSS regularly" }
              ].map((opt) => (
                <div
                  key={opt.val}
                  onClick={() => setSkillLevel(opt.val as SkillLevel)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    skillLevel === opt.val ? "border-primary bg-primary/10" : "hover:border-gray-400"
                  }`}
                >
                  <h3 className="font-semibold">{opt.title}</h3>
                  <p className="text-sm text-muted-foreground">{opt.desc}</p>
                </div>
              ))}
            </CardContent>
            <CardFooter className="flex justify-between mt-4">
              <Button variant="ghost" onClick={() => setStep(2)}>Back</Button>
              <Button onClick={handleComplete} disabled={loading}>
                {loading ? "Saving..." : "Start Contributing"}
              </Button>
            </CardFooter>
          </>
        )}
      </Card>
    </div>
  );
}
