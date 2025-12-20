import type { BlogPost } from "@blog-agent/proto-gen";
import { Badge } from "@blog-agent/ui/components/badge";
import { Calendar, RefreshCcw } from "lucide-react";

interface BlogMetadataProps {
  blogPost: BlogPost;
}

export function BlogMetadata({ blogPost }: BlogMetadataProps) {
  return (
    <header className="mb-10">
      <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground mb-6 font-serif leading-[1.15]">
        {blogPost.title || "無標題"}
      </h1>

      {blogPost.summary && (
        <p className="text-xl text-muted-foreground mb-8 leading-relaxed font-serif italic border-l-4 border-primary/20 pl-6">
          {blogPost.summary}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
        {blogPost.tags && blogPost.tags.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {blogPost.tags.map((tag, idx) => (
              <Badge
                key={idx}
                variant="default"
                className="px-3 py-0.5 rounded-full font-semibold tracking-wide text-[11px] uppercase"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4">
          {blogPost.createdAt && (
            <time dateTime={blogPost.createdAt} className="flex items-center gap-1.5 font-medium">
              <Calendar className="w-4 h-4 text-primary/60" />
              {new Date(blogPost.createdAt).toLocaleDateString("zh-TW", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          )}

          {blogPost.updatedAt && blogPost.updatedAt !== blogPost.createdAt && (
            <time dateTime={blogPost.updatedAt} className="flex items-center gap-1.5 font-medium border-l pl-4 border-muted">
              <RefreshCcw className="w-4 h-4 text-primary/60" />
              <span className="opacity-70">更新於</span>{" "}
              {new Date(blogPost.updatedAt).toLocaleDateString("zh-TW", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          )}
        </div>
      </div>
    </header>
  );
}
