import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileImageIcon } from "lucide-react";
import { Citation } from "../../../../../types";
import { AiCitation } from "./AiCitation";

const THEME = {
  p: ({ children }: any) => (
    <span className="inline leading-relaxed">{children}</span>
  ),
  code: ({ children }: any) => (
    <code className="bg-slate-200 px-1.5 py-0.5 rounded-sm text-sm font-mono text-primary-light">
      {children}
    </code>
  ),

  img: ({ src, alt }: any) => {
    const imageUrl = src?.startsWith("http")
      ? src
      : `http://localhost:8000/api/v1/sessions/download/${encodeURIComponent(
          src
        )}`;

    return (
      <div className="my-8 block group select-none">
        <div
          className={`relative overflow-hidden border border-zinc-200 shadow-sm bg-white transition-all hover:shadow-md ${
            alt ? "rounded-t-2xl border-b-0" : "rounded-2xl"
          }`}
        >
          <img
            src={imageUrl}
            alt={alt}
            className="w-full h-auto object-cover bg-zinc-50 transition-transform duration-700 group-hover:scale-105"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-zinc-900/0 group-hover:bg-zinc-900/5 transition-colors pointer-events-none"></div>
        </div>

        {alt && (
          <div className="bg-zinc-50/80 backdrop-blur-sm border border-zinc-200 rounded-b-2xl px-5 py-3 flex items-start gap-3">
            <div className="mt-0.5 p-1.5 bg-white rounded-md border border-zinc-100 shadow-sm shrink-0">
              <FileImageIcon size={14} className="text-zinc-500" />
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[9px] font-black uppercase tracking-widest text-zinc-400 leading-none">
                Illustration in text
              </span>
              <p className="text-xs font-bold text-zinc-700 leading-tight mt-1">
                {alt}
              </p>
            </div>
          </div>
        )}
      </div>
    );
  },

  ul: ({ children }: any) => (
    <ul className="list-disc ml-4 my-2">{children}</ul>
  ),
  ol: ({ children }: any) => (
    <ol className="list-decimal ml-4 my-2">{children}</ol>
  ),
};

interface Props {
  content: string;
  citations: Citation[];
  idMap: Record<number, number>;
  onDownload: (uuid: string, name: string) => void;
}

export const AiMarkdown = ({
  content,
  citations,
  idMap,
  onDownload,
}: Props) => {
  const parts = content.split(/(\[[\d,\s]+\])/g);

  return (
    <div className="markdown-content inline text-zinc-800">
      {parts.map((part, index) => {
        const isCitation = /^\[[\d,\s]+\]$/.test(part);

        if (isCitation) {
          const originalIds = part
            .replace(/[\[\]]/g, "")
            .split(",")
            .map((s) => parseInt(s.trim()))
            .filter((n) => !isNaN(n));

          const displayIds = Array.from(
            new Set(originalIds.map((id) => idMap[id]).filter(Boolean))
          );

          if (displayIds.length === 0) return null;

          return (
            <span
              key={`cite-group-${index}`}
              className="inline-flex gap-0.5 align-baseline mx-0.5"
            >
              {displayIds.map((dId) => {
                const citation = citations.find((c) => idMap[c.id] === dId);
                if (!citation) return null;

                return (
                  <AiCitation
                    key={dId}
                    displayId={dId}
                    citation={citation}
                    onAction={() =>
                      citation.type === "web"
                        ? window.open(citation.url, "_blank")
                        : onDownload(citation.uuid_name, citation.filename)
                    }
                  />
                );
              })}
            </span>
          );
        }

        return (
          <span key={`text-${index}`} className="inline">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={THEME}>
              {part}
            </ReactMarkdown>
          </span>
        );
      })}
    </div>
  );
};
