"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@blog-agent/ui/components/dialog";
import { Button } from "@blog-agent/ui/components/button";
import { Input } from "@blog-agent/ui/components/input";
import { Label } from "@blog-agent/ui/components/label";

interface CompressionLimitFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (limit: number) => void;
  isLoading?: boolean;
}

export function CompressionLimitForm({
  open,
  onOpenChange,
  onSubmit,
  isLoading = false,
}: CompressionLimitFormProps) {
  const [limit, setLimit] = useState<number>(5000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(limit);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>事實提取設定</DialogTitle>
          <DialogDescription>
            請設定提取後內容的最大字數限制。系統將嘗試在限制內提取核心事實。
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="limit" className="text-right">
                最大字數
              </Label>
              <Input
                id="limit"
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 0)}
                className="col-span-3"
                min={100}
                max={20000}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              取消
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "提取中..." : "開始提取並複製"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

