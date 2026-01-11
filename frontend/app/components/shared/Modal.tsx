import { motion, AnimatePresence } from "framer-motion";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  maxWidth?: string;
  zIndex?: string;
}

export const Modal = ({
  isOpen,
  onClose,
  children,
  maxWidth = "max-w-sm",
  zIndex = "z-[120]",
}: ModalProps) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className={`fixed inset-0 ${zIndex} flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 cursor-pointer`}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className={`bg-zinc-900 border border-zinc-800 w-full ${maxWidth} rounded-2xl shadow-2xl overflow-hidden cursor-default`}
        >
          {children}
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);
