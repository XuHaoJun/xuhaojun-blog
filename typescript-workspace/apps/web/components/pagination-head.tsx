/**
 * 分頁 SEO 連結元件
 * Renders <link rel="prev/next"> tags for pagination SEO
 * React 19 automatically hoists link tags to document head
 */

import type { PaginationInfo } from "@/lib/pagination";

interface PaginationHeadProps {
  pagination: PaginationInfo;
  isHomePage?: boolean;
}

/**
 * 取得頁面路徑
 */
function getPageHref(page: number): string {
  return `/page/${page}`;
}

export function PaginationHead({
  pagination,
  isHomePage = false,
}: PaginationHeadProps) {
  const { currentPage, hasPrevious, hasNext } = pagination;

  return (
    <>
      {hasPrevious && (
        <link rel="prev" href={getPageHref(currentPage - 1)} />
      )}
      {hasNext && (
        <link rel="next" href={getPageHref(currentPage + 1)} />
      )}
    </>
  );
}

