import { ExternalLink, FileText } from "lucide-react";
import { Citation } from "../../../../../types";

interface Props {
  displayId: number;
  citation: Citation;
  onAction: () => void;
}

export const AiCitation = ({ displayId, citation, onAction }: Props) => {
  const isWeb = citation.type === "web";

  return (
    <div className="relative group/num inline-block mx-0.5">
      <button
        onClick={(e) => {
          e.stopPropagation();
          onAction();
        }}
        className={`inline-flex items-center justify-center w-4 h-4 rounded-[4px] text-[9px] font-black transition-all hover:scale-110 active:scale-95 cursor-pointer
          ${
            isWeb
              ? "bg-blue-200 text-blue-600 shadow-sm"
              : "bg-zinc-200 text-zinc-600 shadow-sm"
          }`}
      >
        {displayId}
      </button>

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-zinc-800 text-white text-[11px] rounded-xl opacity-0 invisible group-hover/num:opacity-100 group-hover/num:visible transition-all z-50 shadow-xl border border-zinc-700 pointer-events-none">
        <div className="flex items-center gap-2 mb-1.5 border-b border-zinc-700 pb-1.5">
          {isWeb ? (
            <ExternalLink size={22} className="text-blue-400" />
          ) : (
            <FileText size={12} className="text-zinc-400" />
          )}
          {isWeb ? (
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold truncate uppercase tracking-tighter text-blue-300 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {citation.filename}
            </a>
          ) : (
            <span className="font-bold truncate uppercase tracking-tighter">
              {citation.filename}
            </span>
          )}
        </div>
        <p className="leading-relaxed text-zinc-300 line-clamp-4 italic">
          "{citation.snippet}"
        </p>
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-zinc-900 rotate-45 border-r border-b border-zinc-700"></div>
      </div>
    </div>
  );
};
