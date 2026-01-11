import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, AlertTriangle, X } from "lucide-react";
import { AdminStatus } from "../../../types";

interface Props {
  status: AdminStatus;
  onClose: () => void;
}

export const AdminStatusToast = ({ status, onClose }: Props) => (
  <AnimatePresence>
    {status.type && (
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`fixed bottom-8 right-8 p-4 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border flex items-center gap-3 z-50 min-w-[300px]
          ${
            status.type === "success"
              ? "bg-emerald-950/90 border-emerald-800 text-emerald-100"
              : status.type === "error"
              ? "bg-red-950/90 border-red-800 text-red-100"
              : "bg-zinc-900 border-zinc-700 text-zinc-100"
          }`}
      >
        <div className="shrink-0">
          {status.type === "success" ? (
            <CheckCircle size={20} className="text-emerald-400" />
          ) : status.type === "error" ? (
            <AlertTriangle size={20} className="text-red-400" />
          ) : (
            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          )}
        </div>
        <div className="flex-1 text-xs font-bold uppercase tracking-tight">
          {status.msg}
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-white/10 rounded-lg transition-colors ml-2"
        >
          <X size={16} />
        </button>
      </motion.div>
    )}
  </AnimatePresence>
);
