import * as React from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-text2">{label}</label>
      {children}
    </div>
  );
}

export function TInput({ className, ...props }: React.ComponentProps<typeof Input>) {
  return <Input className={cn("bg-surface2 border-border text-text", className)} {...props} />;
}
