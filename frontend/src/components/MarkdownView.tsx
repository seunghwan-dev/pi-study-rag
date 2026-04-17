import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ReactNode } from "react";

interface Props {
  content: string;
  className?: string;
  onCitationClick?: (index: number) => void;
}

function renderWithCitations(text: string, onClick?: (n: number) => void): ReactNode[] {
  if (!onClick) return [text];

  const parts: ReactNode[] = [];
  const regex = /\[(\d+(?:\s*,\s*\d+)*)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const numbers = match[1].split(",").map((n) => parseInt(n.trim(), 10));
    numbers.forEach((n, idx) => {
      parts.push(
        <button
          key={`cite-${key++}`}
          onClick={() => onClick(n)}
          className="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 mx-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-semibold hover:bg-blue-200 dark:hover:bg-blue-900/60 transition-colors cursor-pointer align-middle"
          title={`参照元 ${n}`}
        >
          [{n}]{idx < numbers.length - 1 ? "," : ""}
        </button>,
      );
    });

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

function processChildren(children: ReactNode, onClick?: (n: number) => void): ReactNode {
  if (!onClick) return children;
  if (typeof children === "string") {
    return renderWithCitations(children, onClick);
  }
  if (Array.isArray(children)) {
    return children.map((child, i) =>
      typeof child === "string" ? (
        <span key={i}>{renderWithCitations(child, onClick)}</span>
      ) : (
        child
      ),
    );
  }
  return children;
}

export default function MarkdownView({ content, className = "", onCitationClick }: Props) {
  return (
    <div className={`prose prose-sm dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => (
            <p className="my-2 leading-relaxed">{processChildren(children, onCitationClick)}</p>
          ),
          ul: ({ children }) => <ul className="my-2 ml-5 list-disc">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 ml-5 list-decimal">{children}</ol>,
          li: ({ children }) => (
            <li className="my-1">{processChildren(children, onCitationClick)}</li>
          ),
          h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mt-3 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-bold mt-3 mb-1">{children}</h3>,
          code: ({ children, className: cn }) =>
            cn ? (
              <code className="block bg-gray-100 dark:bg-gray-900 p-2 rounded text-xs font-mono overflow-x-auto">
                {children}
              </code>
            ) : (
              <code className="bg-gray-100 dark:bg-gray-900 px-1 rounded text-xs font-mono">
                {children}
              </code>
            ),
          strong: ({ children }) => <strong className="font-bold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          table: ({ children }) => (
            <table className="my-3 border-collapse text-sm">{children}</table>
          ),
          th: ({ children }) => (
            <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-800">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">{children}</td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
