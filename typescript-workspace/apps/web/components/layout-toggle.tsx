"use client";

import { useEffect, useState } from "react";
import { Button } from "@blog-agent/ui/components/button";
import { Maximize, Minimize } from "lucide-react";
import { useLayout } from "@/context/layout-context";

export function LayoutToggle() {
  const { isFullWidth, toggleFullWidth } = useLayout();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" disabled>
        <span className="sr-only">切換佈局</span>
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleFullWidth}
      className="rounded-full h-10 w-10 hover:bg-muted"
      aria-label={isFullWidth ? "切換到容器模式" : "切換到滿版模式"}
    >
      {isFullWidth ? (
        <Minimize className="h-[1.2rem] w-[1.2rem]" />
      ) : (
        <Maximize className="h-[1.2rem] w-[1.2rem]" />
      )}
      <span className="sr-only">切換佈局</span>
    </Button>
  );
}

