import { Files } from "lucide-react";

interface Props {
  files: string[];
  isUser: boolean;
  getFileIcon: (n: string) => React.ReactNode;
  setViewingAttachments: (f: string[] | null) => void;
}

export const AttachmentList = ({
  files,
  isUser,
  getFileIcon,
  setViewingAttachments,
}: Props) => {
  if (!files || files.length === 0) return null;

  const displayLimit = 4;
  const shouldCollapse = files.length > displayLimit;
  const visibleFiles = shouldCollapse ? files.slice(0, 3) : files;
  const remainingCount = files.length - 3;

  return (
    <div
      className={`grid grid-cols-2 gap-2 mb-2 w-full max-w-[300px] ${
        isUser ? "ml-auto" : "mr-auto"
      }`}
    >
      {visibleFiles.map((fileName, i) => (
        <div
          key={i}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border truncate select-none shadow-sm
            ${
              isUser
                ? "bg-white border-zinc-200 text-zinc-800"
                : "bg-zinc-800 border-zinc-700 text-zinc-300"
            }`}
          title={fileName}
        >
          <div className="shrink-0">{getFileIcon(fileName)}</div>
          <span className="truncate">{fileName}</span>
        </div>
      ))}

      {shouldCollapse && (
        <button
          onClick={() => setViewingAttachments(files)}
          className={`flex items-center justify-center gap-1 px-3 py-2 rounded-lg text-xs font-bold border transition-colors cursor-pointer
            ${
              isUser
                ? "bg-zinc-100 border-zinc-200 text-zinc-600 hover:bg-zinc-200"
                : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700"
            }`}
        >
          <Files size={14} /> +{remainingCount} files
        </button>
      )}
    </div>
  );
};
