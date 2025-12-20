"use client";

import { useLayout } from "@/context/layout-context";
import { cn } from "@/lib/utils";

interface LayoutContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function LayoutContainer({ children, className }: LayoutContainerProps) {
  const { isFullWidth } = useLayout();

  return (
    <div
      className={cn(
        "transition-all duration-200",
        isFullWidth ? "w-full max-w-none" : "container mx-auto",
        className
      )}
    >
      {children}
    </div>
  );
}

