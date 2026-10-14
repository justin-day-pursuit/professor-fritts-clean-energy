/**
 * Multi-line text box shared by the chat send field and the intake form.
 * ChatPanel and IntakeForm already import { Textarea } from this file — the
 * chat box, energy-goal, and critical-loads rows all render this component.
 * Keep labels, layout, and send-on-Enter in those files. Change height,
 * border, or disabled styles here if the design system shifts. Base UI has
 * no textarea primitive, so this follows the official shadcn base-nova
 * pattern (native textarea + cn), same as input.tsx besides that primitive.
 */
import * as React from "react"
import { cn } from "cn"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-base transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
