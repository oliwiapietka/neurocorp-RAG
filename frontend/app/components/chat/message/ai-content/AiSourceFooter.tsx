import { BookOpen, ExternalLink, FileText, Download } from "lucide-react";
import { Citation } from "../../../../../types";

interface Props {
  citations: Citation[];
  fileToIdMap: Map<string, number>;
  content: string;
  onDownload: (uuid: string, name: string) => void;
}

export const AiSourceFooter = ({
  citations,
  fileToIdMap,
  content,
  onDownload,
}: Props) => {
  const usedIdsInText = new Set<number>(
    Array.from(content.matchAll(/\[([\d,\s]+)\]/g))
      .flatMap((m) => m[1].split(",").map((s) => parseInt(s.trim(), 10)))
      .filter((n) => !Number.isNaN(n))
  );

  const uniqueDocs = Array.from(
    new Map(citations.map((c) => [c.uuid_name, c])).values()
  ).filter((c) => {
    const originalIdsOfThisFile = citations
      .filter((allC) => allC.uuid_name === c.uuid_name)
      .map((allC) => allC.id);
    return originalIdsOfThisFile.some((id) => usedIdsInText.has(id));
  });

  if (uniqueDocs.length === 0) return null;

  return (
    <div className="mt-2 pt-3 border-t border-zinc-200/30">
      <p className="text-[10px] uppercase font-bold text-zinc-500 mb-2 flex items-center gap-1 tracking-widest">
        <BookOpen size={12} /> Knowledge Sources:
      </p>
      <div className="flex flex-wrap gap-2">
        {uniqueDocs.map((citation) => {
          const isWeb = citation.type === "web";
          const displayId = fileToIdMap.get(citation.uuid_name);

          return (
            <div
              key={citation.uuid_name}
              className={`group flex items-center gap-2 px-2 py-1.5 border rounded-lg text-[11px] font-medium transition-all shadow-sm
                ${
                  isWeb
                    ? "border-blue-200 text-blue-600 hover:bg-blue-100"
                    : "bg-zinc-50 border-zinc-300 text-zinc-600 hover:bg-zinc-200"
                }`}
            >
              <div
                className="flex items-center gap-2 cursor-pointer"
                onClick={() =>
                  isWeb
                    ? window.open(citation.url, "_blank")
                    : onDownload(citation.uuid_name, citation.filename)
                }
              >
                <span
                  className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-black ${
                    isWeb
                      ? "bg-blue-200 text-blue-600"
                      : "bg-zinc-200 text-zinc-700"
                  }`}
                >
                  {displayId}
                </span>
                {isWeb ? <ExternalLink size={13} /> : <FileText size={13} />}
                <span className="truncate max-w-[150px] font-semibold">
                  {citation.filename}
                </span>
              </div>
              <button
                className="ml-1 opacity-40 hover:opacity-100 cursor-pointer"
                onClick={() =>
                  isWeb
                    ? window.open(citation.url, "_blank")
                    : onDownload(citation.uuid_name, citation.filename)
                }
              >
                {isWeb ? <ExternalLink size={14} /> : <Download size={14} />}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
