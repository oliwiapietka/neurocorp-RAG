import { X, Files, Download } from "lucide-react";
import { Modal } from "../shared/Modal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  attachments: string[] | null;
  getFileIcon: (n: string) => React.ReactNode;
  handleDownload: (uuid: string, name: string) => Promise<void>;
}

export const AttachmentViewerModal = ({
  isOpen,
  onClose,
  attachments,
  getFileIcon,
  handleDownload,
}: Props) => (
  <Modal isOpen={isOpen} onClose={onClose} maxWidth="max-w-lg" zIndex="z-[150]">
    <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
      <div className="flex items-center gap-2">
        <Files size={18} className="text-primary" />
        <h3 className="font-semibold text-zinc-100">
          Attached files ({attachments?.length || 0})
        </h3>
      </div>
      <button
        onClick={onClose}
        className="p-1.5 hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-white transition-colors cursor-pointer"
      >
        <X size={20} />
      </button>
    </div>
    <div className="p-4 overflow-y-auto custom-scrollbar bg-zinc-950/30 max-h-[50vh]">
      <div className="grid gap-2">
        {attachments?.map((fileName, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-2 bg-zinc-800 rounded-lg"
          >
            <div className="flex items-center gap-2">
              {getFileIcon(fileName)}
              <span className="text-sm truncate text-zinc-300">{fileName}</span>
            </div>
            <button
              onClick={() => handleDownload(fileName, fileName)}
              className="p-4 hover:bg-zinc-700 rounded-full text-primary transition-colors cursor-pointer"
            ></button>
          </div>
        ))}
      </div>
    </div>
    <div className="p-4 border-t border-zinc-800 bg-zinc-900">
      <button
        onClick={onClose}
        className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-sm font-medium transition-colors cursor-pointer"
      >
        Close
      </button>
    </div>
  </Modal>
);
