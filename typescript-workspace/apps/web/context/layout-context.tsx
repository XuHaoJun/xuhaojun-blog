"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface LayoutContextType {
  isFullWidth: boolean;
  toggleFullWidth: () => void;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [isFullWidth, setIsFullWidth] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Load preference from localStorage
    const saved = localStorage.getItem("layout-full-width");
    if (saved === "true") {
      setIsFullWidth(true);
    }
  }, []);

  const toggleFullWidth = () => {
    const newValue = !isFullWidth;
    setIsFullWidth(newValue);
    if (mounted) {
      localStorage.setItem("layout-full-width", String(newValue));
    }
  };

  // Always provide context, but use default values before mounting to prevent hydration mismatch
  return (
    <LayoutContext.Provider value={{ isFullWidth, toggleFullWidth }}>
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayout() {
  const context = useContext(LayoutContext);
  if (context === undefined) {
    throw new Error("useLayout must be used within a LayoutProvider");
  }
  return context;
}

