import { motion, AnimatePresence } from "framer-motion";
import { Files, ChevronDown, ChevronUp, X } from "lucide-react";

interface Props {
  selectedFiles: File[];
  isExpanded: boolean;
  setIsExpanded: (v: boolean) => void;
  removeFile: (i: number) => void;
  clearAll: (e: React.MouseEvent) => void;
  getFileIcon: (n: string) => React.ReactNode;
}

export const FilePreview = ({
  selectedFiles,
  isExpanded,
  setIsExpanded,
  removeFile,
  clearAll,
  getFileIcon,
}: Props) => {
  if (selectedFiles.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="w-full"
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between bg-zinc-800 border border-zinc-700 p-2 rounded-xl mb-1 cursor-pointer hover:bg-zinc-700/80 transition-colors"
      >
        <div className="flex items-center gap-2 text-sm text-zinc-300 pl-2">
          <Files size={16} className="text-primary" />
          <span className="font-medium">
            Selected {selectedFiles.length} files
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={clearAll}
            className="p-1.5 text-xs text-zinc-500 hover:text-red-400 transition-colors mr-2"
          >
            Clear
          </button>
          {isExpanded ? (
            <ChevronDown size={18} className="text-zinc-400" />
          ) : (
            <ChevronUp size={18} className="text-zinc-400" />
          )}
        </div>
      </div>

      {(isExpanded || selectedFiles.length <= 3) && (
        <div className="flex flex-wrap gap-2 max-h-[150px] overflow-y-auto custom-scrollbar p-1">
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 bg-zinc-800/50 border border-zinc-700/50 pl-3 pr-2 py-2 rounded-lg text-sm text-zinc-300 shadow-sm"
            >
              {getFileIcon(file.name)}
              <span className="max-w-[120px] truncate text-xs">
                {file.name}
              </span>
              <button
                onClick={() => removeFile(index)}
                className="p-1 hover:bg-zinc-700 rounded-full text-zinc-500 hover:text-red-400"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
};
