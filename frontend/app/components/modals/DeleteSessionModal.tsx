import { Trash2 } from "lucide-react";
import { Modal } from "../shared/Modal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const DeleteSessionModal = ({ isOpen, onClose, onConfirm }: Props) => (
  <Modal isOpen={isOpen} onClose={onClose}>
    <div className="p-6 text-center">
      <div className="w-12 h-12 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-900/30">
        <Trash2 size={24} className="text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-zinc-100 mb-2">Delete Chat?</h3>
      <p className="text-sm text-zinc-400 mb-6">
        This operation is irreversible.
      </p>
      <div className="flex gap-3">
        <button
          onClick={onClose}
          className="flex-1 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded-xl text-sm font-medium transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 py-2.5 bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-900/30 rounded-xl text-sm font-medium transition-all cursor-pointer"
        >
          Delete Chat
        </button>
      </div>
    </div>
  </Modal>
);
