"use client";

import { useEffect, useState, useRef } from "react";

interface UseIntersectionObserverOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number | number[];
  enabled?: boolean;
}

/**
 * Custom hook for observing element intersection with viewport
 * Returns the ID/index of the currently visible element
 * Supports both string IDs (for blocks) and number indices (for messages)
 */
export function useIntersectionObserver(
  elementIds: (string | number)[],
  options: UseIntersectionObserverOptions = {}
): number | string | undefined {
  const [activeId, setActiveId] = useState<string | number | undefined>();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const elementRefs = useRef<Map<string | number, Element>>(new Map());

  const {
    root = null,
    rootMargin = "-20% 0px -60% 0px", // Trigger when element is in top 40% of viewport
    threshold = 0.1,
    enabled = true,
  } = options;

  useEffect(() => {
    if (!enabled || elementIds.length === 0) {
      return;
    }

    // Clean up previous observer
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    // Create new observer
    observerRef.current = new IntersectionObserver(
      (entries) => {
        // Find the entry with the highest intersection ratio
        let maxRatio = 0;
        let maxEntry: IntersectionObserverEntry | null = null;

        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > maxRatio) {
            maxRatio = entry.intersectionRatio;
            maxEntry = entry;
          }
        });

        if (maxEntry) {
          const targetId = maxEntry.target.id;
          // Check if it's a message (message-{index}) or block (block-{id})
          if (targetId.startsWith("message-")) {
            const index = parseInt(targetId.replace("message-", ""), 10);
            if (!isNaN(index)) {
              setActiveId(index);
            }
          } else if (targetId.startsWith("block-")) {
            const id = targetId.replace("block-", "");
            setActiveId(id);
          }
        }
      },
      {
        root,
        rootMargin,
        threshold,
      }
    );

    // Observe all elements
    elementIds.forEach((id) => {
      // Support both message-{index} and block-{id} formats
      const elementId = typeof id === "number" ? `message-${id}` : `block-${id}`;
      const element = document.getElementById(elementId);
      if (element) {
        elementRefs.current.set(id, element);
        observerRef.current?.observe(element);
      }
    });

    // Cleanup
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [elementIds, root, rootMargin, threshold, enabled]);

  return activeId;
}

