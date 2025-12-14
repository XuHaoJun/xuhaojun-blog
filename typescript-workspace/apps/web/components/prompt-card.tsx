"use client";

import { useState } from "react";
import type { PromptMeta, PromptCandidate } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import { DiffHighlighter } from "./diff-highlighter";
import { SimulationModal } from "./simulation-modal";
import { MyReactMarkdown } from "./my-react-markdown";

interface PromptCardProps {
  promptMeta: PromptMeta;
  className?: string;
  messageNumber?: number;
  onScrollToMessage?: () => void;
}

export function PromptCard({ 
  promptMeta, 
  className, 
  messageNumber,
  onScrollToMessage 
}: PromptCardProps) {
  const [activeTab, setActiveTab] = useState(0);
  const [isSimulationOpen, setIsSimulationOpen] = useState(false);
  const candidates = promptMeta.betterCandidates || [];

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div
      className={cn(
        "bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm",
        className
      )}
    >
      {/* 1. 🔴 原始提問 (The User's Attempt) */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <div className="text-sm font-semibold mb-2 flex items-center gap-2">
          <span>👤</span>
          <span className="text-blue-700 dark:text-blue-300">使用者</span>
          {messageNumber !== undefined && (
            <button
              onClick={onScrollToMessage}
              className="ml-auto text-xs text-gray-400 dark:text-gray-500 hover:text-blue-500 dark:hover:text-blue-400 transition-colors cursor-pointer font-normal"
              title="跳至對應訊息"
            >
              #{messageNumber}
            </button>
          )}
        </div>
        <div className="prose prose-sm dark:prose-invert max-w-none font-serif">
          <MyReactMarkdown content={promptMeta.originalPrompt} />
        </div>
      </div>

      {/* 2. 🧐 AI 診斷 (The Critique) */}
      {promptMeta.analysis && (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-yellow-700 dark:text-yellow-400 font-semibold">🧐 AI 診斷</span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none font-serif">
            <MyReactMarkdown content={promptMeta.analysis} />
          </div>
        </div>
      )}

      {/* 3. 🟢 優化建議 (The Better Candidates) */}
      {candidates.length > 0 && (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 border-b border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-green-700 dark:text-green-400 font-semibold">🟢 優化建議</span>
          </div>

          {/* Tab Navigation */}
          {candidates.length > 1 && (
            <div className="flex gap-2 mb-3 border-b border-green-200 dark:border-green-800">
              {candidates.map((candidate, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  className={cn(
                    "px-3 py-2 text-sm font-medium transition-colors",
                    activeTab === idx
                      ? "text-green-700 dark:text-green-400 border-b-2 border-green-600 dark:border-green-400"
                      : "text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-300"
                  )}
                >
                  {getCandidateTypeLabel(candidate.type)}
                </button>
              ))}
            </div>
          )}

          {/* Active Candidate Content */}
          {candidates[activeTab] && (
            <div className="space-y-3">
              <div className="bg-white dark:bg-gray-900 rounded p-3 border border-green-200 dark:border-green-800">
                {candidates[activeTab].prompt}
              </div>

              {candidates[activeTab].reasoning && (
                <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                  {candidates[activeTab].reasoning}
                </p>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(candidates?.[activeTab]?.prompt ?? "")}
                  className="flex-1 px-3 py-2 text-sm bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600 text-white rounded transition-colors"
                >
                  📋 複製此 Prompt
                </button>
                <button
                  onClick={() => setIsSimulationOpen(true)}
                  className="flex-1 px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600 text-white rounded transition-colors"
                >
                  🚀 模擬運行
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Simulation Modal */}
      {candidates[activeTab] && (
        <SimulationModal
          prompt={candidates[activeTab].prompt}
          isOpen={isSimulationOpen}
          onClose={() => setIsSimulationOpen(false)}
        />
      )}

      {/* 4. 🚀 預期效果 (Why it works) */}
      {promptMeta.expectedEffect && (
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-gray-700 dark:text-gray-300 font-semibold text-sm">
              🚀 預期效果
            </span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none font-serif">
            <MyReactMarkdown content={promptMeta.expectedEffect} />
          </div>
        </div>
      )}
    </div>
  );
}

function getCandidateTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    structured: "結構化版",
    "role-play": "角色扮演版",
    "chain-of-thought": "思維鏈版",
    "step-by-step": "結構化",
    "expert-persona": "角色化",
    minimalist: "簡潔化",
  };
  return labels[type] || type;
}
