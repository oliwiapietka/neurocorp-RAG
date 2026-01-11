import {
  UploadCloud,
  Files,
  ChevronDown,
  ChevronUp,
  FileText,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  adminFiles: File[];
  isExpanded: boolean;
  setIsExpanded: (v: boolean) => void;
  setAdminFiles: (f: File[]) => void;
  removeFile: (i: number) => void;
  onUpload: () => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export const AdminUploadZone = (props: Props) => (
  <section className="mb-12">
    <h2 className="text-lg font-semibold text-zinc-500 mb-4 flex items-center gap-2">
      <UploadCloud size={20} /> Add Documents
    </h2>
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 hover:border-zinc-700 transition-colors">
      <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-zinc-700 border-dashed rounded-xl cursor-pointer hover:bg-zinc-800/50 hover:border-zinc-700 transition-all group">
        <div className="flex flex-col items-center justify-center pt-5 pb-6 text-zinc-600 group-hover:text-zinc-400 transition-colors">
          <UploadCloud size={32} className="mb-2" />
          <p className="mb-1 text-sm">
            <span className="font-semibold">Click</span> to upload files
          </p>
          <p className="text-xs">PDF, TXT, DOCX</p>
        </div>
        <input
          type="file"
          multiple
          ref={props.fileInputRef}
          onChange={props.onFileSelect}
          className="hidden"
          accept=".pdf,.txt,.docx"
        />
      </label>

      {props.adminFiles.length > 0 && (
        <div className="mt-6 flex flex-col items-center w-full">
          <div className="w-full max-w-md flex flex-col gap-2">
            <div
              onClick={() => props.setIsExpanded(!props.isExpanded)}
              className="flex items-center justify-between bg-zinc-800 border border-zinc-700 p-2.5 rounded-xl cursor-pointer hover:bg-zinc-700/80 transition-colors w-full"
            >
              <div className="flex items-center gap-2 text-xs text-zinc-400 pl-1">
                <Files size={14} className="text-primary" />
                <span className="font-medium text-zinc-300">
                  {props.adminFiles.length === 1
                    ? "Selected 1 file"
                    : `Selected ${props.adminFiles.length} files`}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    props.setAdminFiles([]);
                  }}
                  className="text-[10px] text-zinc-500 hover:text-red-400 px-2 py-1 rounded transition-colors cursor-pointer font-medium"
                >
                  Clear
                </button>
                {props.isExpanded ? (
                  <ChevronDown size={16} className="text-zinc-500" />
                ) : (
                  <ChevronUp size={16} className="text-zinc-500" />
                )}
              </div>
            </div>

            <AnimatePresence>
              {props.isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar p-1 mb-2">
                    {props.adminFiles.map((f, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between bg-zinc-800/30 p-2 rounded-lg text-xs border border-zinc-800 hover:border-zinc-700 transition-colors group"
                      >
                        <div className="flex items-center gap-2 text-zinc-400 truncate pr-4">
                          <FileText
                            size={14}
                            className="text-zinc-500 shrink-0"
                          />
                          <span className="truncate">{f.name}</span>
                        </div>
                        <button
                          onClick={() => props.removeFile(i)}
                          className="p-1 hover:bg-zinc-700 rounded-full transition-colors text-zinc-500 hover:text-red-400 cursor-pointer"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <button
              onClick={props.onUpload}
              className="w-full bg-zinc-900 hover:bg-black text-xs text-zinc-400 font-medium border border-zinc-700 py-3 rounded-xl transition-all shadow-lg cursor-pointer flex items-center justify-center gap-2 active:scale-[0.98]"
            >
              <UploadCloud size={16} className="text-primary" /> Ingest{" "}
              {props.adminFiles.length} files to Database
            </button>
          </div>
        </div>
      )}
    </div>
  </section>
);
