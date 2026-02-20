import { useState } from "react"
import { Star } from "lucide-react"
import { cn } from "@/lib/utils"

interface StarRatingInputProps {
  value: number
  onChange: (rating: number) => void
  maxStars?: number
  size?: number
  className?: string
}

export function StarRatingInput({
  value,
  onChange,
  maxStars = 5,
  size = 24,
  className,
}: StarRatingInputProps) {
  const [hover, setHover] = useState<number | null>(null)
  const display = hover ?? value

  return (
    <span
      className={cn("inline-flex cursor-pointer gap-0.5", className)}
      onMouseLeave={() => setHover(null)}
    >
      {Array.from({ length: maxStars }).map((_, i) => {
        const starValue = i + 1
        const filled = starValue <= display
        return (
          <button
            key={i}
            type="button"
            onClick={() => onChange(starValue)}
            onMouseEnter={() => setHover(starValue)}
            className="p-0.5 transition-transform hover:scale-110"
            aria-label={`${starValue} estrella${starValue > 1 ? "s" : ""}`}
          >
            <Star
              size={size}
              className={cn(
                "transition-colors",
                filled ? "fill-amber-400 text-amber-400" : "text-amber-400/30"
              )}
            />
          </button>
        )
      })}
    </span>
  )
}
