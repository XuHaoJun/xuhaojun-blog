/**
 * 分頁導覽元件
 * Blog pagination component wrapping shadcn/ui pagination
 */

import Link from "next/link";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@blog-agent/ui/components/pagination";
import type { PaginationInfo } from "@/lib/pagination";
import { getPageNumbers } from "@/lib/pagination";

interface BlogPaginationProps {
  pagination: PaginationInfo;
  isHomePage?: boolean;
}

/**
 * 取得頁面路徑
 * 首頁時，page 1 連結到 /page/1（不是 /）
 */
function getPageHref(page: number): string {
  return `/page/${page}`;
}

export function BlogPagination({ pagination, isHomePage = false }: BlogPaginationProps) {
  const { currentPage, totalPages, hasPrevious, hasNext } = pagination;

  // 只有一頁時不顯示分頁
  if (totalPages <= 1) {
    return null;
  }

  const pageNumbers = getPageNumbers(currentPage, totalPages);

  return (
    <Pagination className="mt-8">
      <PaginationContent>
        {/* Previous 按鈕 */}
        {hasPrevious && (
          <PaginationItem>
            <Link href={getPageHref(currentPage - 1)} legacyBehavior passHref>
              <PaginationPrevious />
            </Link>
          </PaginationItem>
        )}

        {/* 頁碼 */}
        {pageNumbers.map((pageNum, idx) => (
          <PaginationItem key={idx}>
            {pageNum === "ellipsis" ? (
              <PaginationEllipsis />
            ) : (
              <Link href={getPageHref(pageNum)} legacyBehavior passHref>
                <PaginationLink isActive={pageNum === currentPage}>
                  {pageNum}
                </PaginationLink>
              </Link>
            )}
          </PaginationItem>
        ))}

        {/* Next 按鈕 */}
        {hasNext && (
          <PaginationItem>
            <Link href={getPageHref(currentPage + 1)} legacyBehavior passHref>
              <PaginationNext />
            </Link>
          </PaginationItem>
        )}
      </PaginationContent>
    </Pagination>
  );
}
