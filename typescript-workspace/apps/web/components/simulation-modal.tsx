"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@blog-agent/ui/components/dialog";
import { Button } from "@blog-agent/ui/components/button";
import { Spinner } from "@blog-agent/ui/components/spinner";

interface SimulationModalProps {
  prompt: string;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Simulation Modal - Shows what AI would respond with the optimized prompt
 * Note: This requires backend API support to actually run the simulation
 */
export function SimulationModal({
  prompt,
  isOpen,
  onClose,
}: SimulationModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [simulationResult, setSimulationResult] = useState<string | null>(null);

  const runSimulation = async () => {
    setIsLoading(true);
    // TODO: Call backend API to run simulation
    // For now, show a placeholder
    setTimeout(() => {
      setSimulationResult(
        "此功能需要後端 API 支援。實際實作時，這裡會顯示使用優化後的 Prompt 時 AI 的實際回應。"
      );
      setIsLoading(false);
    }, 1000);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            🚀 模擬運行
          </DialogTitle>
          <DialogDescription>
            查看 AI 使用優化後的 Prompt 產生的預期回應。
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4 space-y-6">
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">
              使用的 Prompt：
            </h3>
            <div className="bg-muted rounded-md p-3 font-mono text-sm border">
              {prompt}
            </div>
          </div>

          {!simulationResult && !isLoading && (
            <div className="text-center py-12 bg-muted/30 rounded-lg border border-dashed">
              <p className="text-muted-foreground mb-4">
                點擊下方按鈕來模擬 AI 的回應
              </p>
              <Button onClick={runSimulation} variant="default">
                執行模擬
              </Button>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-12">
              <Spinner className="h-8 w-8 mb-4 mx-auto" />
              <p className="text-muted-foreground">
                正在模擬 AI 回應...
              </p>
            </div>
          )}

          {simulationResult && (
            <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-sm font-medium text-muted-foreground">
                AI 回應：
              </h3>
              <div className="bg-primary/5 dark:bg-primary/10 rounded-md p-4 border border-primary/20">
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {simulationResult}
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            關閉
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
