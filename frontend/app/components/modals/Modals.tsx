"use client";
import { DeleteSessionModal } from "./DeleteSessionModal";
import { AttachmentViewerModal } from "./AttachmentViewerModal";
import { Modal } from "../shared/Modal";
import { Database } from "lucide-react";

interface ModalsProps {
  deletingSessionId: string | null;
  setDeletingSessionId: (v: string | null) => void;
  handleActualDelete: () => void;
  isClearingDatabase: boolean;
  setIsClearingDatabase: (v: boolean) => void;
  handleActualClearDatabase: () => void;
  viewingAttachments: string[] | null;
  setViewingAttachments: (f: string[] | null) => void;
  handleDownload: (uuid: string, name: string) => Promise<void>;
  getFileIcon: (n: string) => React.ReactNode;
}

export default function Modals(props: ModalsProps) {
  return (
    <>
      <DeleteSessionModal
        isOpen={!!props.deletingSessionId}
        onClose={() => props.setDeletingSessionId(null)}
        onConfirm={props.handleActualDelete}
      />

      <Modal
        isOpen={props.isClearingDatabase}
        onClose={() => props.setIsClearingDatabase(false)}
      >
        <div className="p-6 text-center">
          <div className="w-12 h-12 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-900/30">
            <Database size={24} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-100 mb-2">
            Are you sure you want to proceed?
          </h3>
          <p className="text-sm text-zinc-400 mb-6">
            This operation will permanently wipe the global knowledge base.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => props.setIsClearingDatabase(false)}
              className="flex-1 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded-xl text-sm font-medium transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={props.handleActualClearDatabase}
              className="flex-1 py-2.5 bg-red-900/20 text-red-400 border border-red-900/30 rounded-xl text-sm font-medium transition-all cursor-pointer"
            >
              Clear All
            </button>
          </div>
        </div>
      </Modal>

      <AttachmentViewerModal
        isOpen={!!props.viewingAttachments}
        onClose={() => props.setViewingAttachments(null)}
        attachments={props.viewingAttachments}
        getFileIcon={props.getFileIcon}
        handleDownload={props.handleDownload}
      />
    </>
  );
}
