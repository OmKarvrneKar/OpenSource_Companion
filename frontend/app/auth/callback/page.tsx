"use client";

import { useEffect, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    const isNewUser = searchParams.get("new_user") === "true";

    if (token) {
      localStorage.setItem("token", token);
      if (isNewUser) {
        router.push("/onboarding");
      } else {
        router.push("/feed");
      }
    } else {
      setError("Authentication failed. No token received.");
      setTimeout(() => router.push("/"), 3000);
    }
  }, [router, searchParams]);

  if (error) {
    return <div className="text-red-500 text-center mt-10">{error}</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <Skeleton className="h-12 w-12 rounded-full animate-spin" />
      <p className="text-muted-foreground animate-pulse">Authenticating with GitHub...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-screen"><Skeleton className="h-20 w-20" /></div>}>
      <CallbackHandler />
    </Suspense>
  );
}
