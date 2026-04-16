"use client";

import { Badge as BadgeType } from "@/types";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Award } from "lucide-react";

interface BadgeShelfProps {
  earnedBadges: BadgeType[];
  allBadges?: unknown[];
}

export default function BadgeShelf({ earnedBadges }: BadgeShelfProps) {
  // If we don't have all badges, we just show earned ones + placeholders
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4">
      <TooltipProvider>
        {earnedBadges.map((badge) => (
          <Tooltip key={badge.id}>
            <TooltipTrigger asChild>
              <div className="flex flex-col items-center gap-2 p-3 rounded-lg border bg-primary/5 hover:bg-primary/10 transition-colors cursor-help">
                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                  {badge.icon_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={badge.icon_url} alt={badge.name} className="w-8 h-8 object-contain" />
                  ) : (
                    <Award className="w-8 h-8" />
                  )}
                </div>
                <span className="text-xs font-semibold text-center leading-tight">{badge.name}</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-semibold">{badge.name}</p>
              <p className="text-xs text-muted-foreground">{badge.description}</p>
            </TooltipContent>
          </Tooltip>
        ))}
        
        {/* Placeholders for locked badges - usually would be dynamic based on allBadges */}
        {earnedBadges.length < 8 && [...Array(8 - earnedBadges.length)].map((_, i) => (
          <div key={`locked-${i}`} className="flex flex-col items-center gap-2 p-3 rounded-lg border border-dashed opacity-40 grayscale">
            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
              <Award className="w-8 h-8" />
            </div>
            <span className="text-xs font-semibold text-center leading-tight">Locked</span>
          </div>
        ))}
      </TooltipProvider>
    </div>
  );
}
