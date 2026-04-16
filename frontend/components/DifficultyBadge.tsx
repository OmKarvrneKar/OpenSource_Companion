import { Badge } from "@/components/ui/badge";
import { SkillLevel } from "@/types";

interface DifficultyBadgeProps {
  difficulty: SkillLevel | string;
}

export default function DifficultyBadge({ difficulty }: DifficultyBadgeProps) {
  const norm = difficulty.toLowerCase() as SkillLevel;
  
  if (norm === "advanced") {
    return <Badge variant="destructive">Advanced</Badge>;
  }
  
  if (norm === "intermediate") {
    return <Badge variant="default" className="bg-yellow-500 hover:bg-yellow-600 text-white">Intermediate</Badge>;
  }
  
  // default to beginner
  return <Badge variant="default" className="bg-green-500 hover:bg-green-600 text-white">Beginner</Badge>;
}
