import { Star } from "lucide-react"
import { cn } from "@/lib/utils"

interface StarRatingProps {
  rating: number
  maxStars?: number
  size?: number
  className?: string
}

export function StarRating({
  rating,
  maxStars = 5,
  size = 16,
  className,
}: StarRatingProps) {
  const rounded = Math.round(rating)
  const full = Math.min(rounded, maxStars)
  const empty = maxStars - full

  return (
    <span className={cn("inline-flex items-center gap-0.5", className)}>
      {Array.from({ length: full }).map((_, i) => (
        <Star key={`full-${i}`} size={size} className="fill-amber-400 text-amber-400" />
      ))}
      {Array.from({ length: empty }).map((_, i) => (
        <Star key={`empty-${i}`} size={size} className="text-amber-400/30" />
      ))}
    </span>
  )
}
