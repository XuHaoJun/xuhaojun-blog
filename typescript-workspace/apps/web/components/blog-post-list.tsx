/**
 * 文章列表元件
 * Blog post list component for paginated pages
 */

import Link from "next/link";
import type { BlogPost } from "@blog-agent/proto-gen";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@blog-agent/ui/components/card";
import { Badge } from "@blog-agent/ui/components/badge";
import { Calendar } from "lucide-react";

interface BlogPostListProps {
  posts: BlogPost[];
}

export function BlogPostList({ posts }: BlogPostListProps) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-12 bg-muted/20 rounded-lg border-2 border-dashed">
        <p className="text-muted-foreground">
          目前還沒有部落格文章。使用 CLI 處理對話紀錄以生成文章。
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {posts.map((post) => (
        <Card key={post.id} className="overflow-hidden transition-all hover:shadow-md border-muted">
          <CardHeader>
            <Link href={`/blog/${post.id}`} className="group">
              <CardTitle className="text-2xl font-bold group-hover:text-primary transition-colors line-clamp-2 leading-tight">
                {post.title || "無標題"}
              </CardTitle>
            </Link>
          </CardHeader>
          
          {post.summary && (
            <CardContent>
              <p className="text-muted-foreground line-clamp-3 leading-relaxed">
                {post.summary}
              </p>
            </CardContent>
          )}
          
          <CardFooter className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t bg-muted/5">
            <div className="flex flex-wrap gap-1.5">
              {post.tags && post.tags.length > 0 ? (
                post.tags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="px-2 py-0 text-[10px] uppercase tracking-wider font-semibold">
                    {tag}
                  </Badge>
                ))
              ) : (
                <Badge variant="outline" className="text-[10px] uppercase tracking-wider opacity-50">
                  Uncategorized
                </Badge>
              )}
            </div>
            
            {post.createdAt && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
                <Calendar className="w-3.5 h-3.5" />
                <time dateTime={post.createdAt}>
                  {new Date(post.createdAt).toLocaleDateString("zh-TW", {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                  })}
                </time>
              </div>
            )}
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
