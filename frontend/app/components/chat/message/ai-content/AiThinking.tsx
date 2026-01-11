import { Bot } from "lucide-react";
import { motion, Variants } from "framer-motion";

export const AiThinking = () => {
  const dotVariants: Variants = {
    animate: (i: number) => ({
      y: [0, -5, 0],
      transition: {
        delay: i * 0.15,
        duration: 0.8,
        repeat: Infinity,
        ease: "easeInOut" as const,
      },
    }),
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4 justify-start mb-6"
    >
      <div className="w-8 h-8 rounded-full bg-zinc-100 border border-zinc-200 flex items-center justify-center shrink-0 mt-1 shadow-sm">
        <Bot size={16} className="text-zinc-600" />
      </div>

      <div className="flex flex-col gap-2">
        <motion.div
          animate={{
            backgroundColor: ["#e4e4e7", "#f4f4f5", "#e4e4e7"],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "linear" as const,
          }}
          className="px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5 shadow-sm border border-zinc-300/50"
        >
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              custom={i}
              variants={dotVariants}
              animate="animate"
              className="w-1.5 h-1.5 bg-zinc-400 rounded-full"
            />
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
};
