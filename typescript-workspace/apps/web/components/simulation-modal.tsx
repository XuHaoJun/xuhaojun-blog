"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

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

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            🚀 模擬運行
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            aria-label="關閉"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              使用的 Prompt：
            </h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 font-mono text-sm">
              {prompt}
            </div>
          </div>

          {!simulationResult && !isLoading && (
            <div className="text-center py-8">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                點擊下方按鈕來模擬 AI 的回應
              </p>
              <button
                onClick={runSimulation}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600 text-white rounded transition-colors"
              >
                執行模擬
              </button>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                正在模擬 AI 回應...
              </p>
            </div>
          )}

          {simulationResult && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                AI 回應：
              </h3>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-4 border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                  {simulationResult}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded transition-colors"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  );
}

