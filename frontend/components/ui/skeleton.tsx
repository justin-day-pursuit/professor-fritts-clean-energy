/**
 * Pulsing placeholder while content loads. Not used on the main planner yet;
 * keep this file so a later loading state can import Skeleton without adding
 * a new primitive. Change the pulse color via bg-muted.
 */
import * as React from "react"
import { cn } from "cn"

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }
