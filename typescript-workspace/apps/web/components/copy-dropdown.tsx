"use client";

import { Copy } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@blog-agent/ui/components/dropdown-menu";
import { Button } from "@blog-agent/ui/components/button";
import { cn } from "@/lib/utils";

interface CopyDropdownProps {
  onCopyCurrent: () => void;
  onCopyOriginal: () => void;
  onCopyCompressed: () => void;
  className?: string;
  buttonVariant?: "ghost" | "default" | "outline" | "secondary";
  buttonSize?: "sm" | "icon" | "default";
  buttonText?: string;
  align?: "start" | "end" | "center";
}

export function CopyDropdown({
  onCopyCurrent,
  onCopyOriginal,
  onCopyCompressed,
  className,
  buttonVariant = "ghost",
  buttonSize = "icon",
  buttonText,
  align = "end",
}: CopyDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={buttonVariant}
          size={buttonSize}
          className={cn(buttonText ? "gap-2" : "h-8 w-8", className)}
          title="複製選項"
        >
          <Copy className="w-4 h-4" />
          {buttonText && <span>{buttonText}</span>}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-auto min-w-max">
        <DropdownMenuItem
          className="cursor-pointer whitespace-nowrap"
          onClick={onCopyCurrent}
        >
          僅複製此訊息
        </DropdownMenuItem>
        <DropdownMenuItem
          className="cursor-pointer whitespace-nowrap"
          onClick={onCopyOriginal}
        >
          複製原始對話 (含完整歷史)
        </DropdownMenuItem>
        <DropdownMenuItem
          className="cursor-pointer whitespace-nowrap"
          onClick={onCopyCompressed}
        >
          複製壓縮對話 (含歷史摘要)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

