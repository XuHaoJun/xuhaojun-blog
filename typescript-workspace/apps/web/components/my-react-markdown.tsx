import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypePrismPlus from "rehype-prism-plus";

interface ReactMarkdownProps {
  content: string;
}

export function MyReactMarkdown({ content }: ReactMarkdownProps) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypePrismPlus]}>
      {content}
    </ReactMarkdown>
  );
}
