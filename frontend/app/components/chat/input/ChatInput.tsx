import { Paperclip, ArrowUp, Send } from "lucide-react";
import { RefObject } from "react";

interface Props {
  input: string;
  setInput: (v: string) => void;
  isLoading: boolean;
  handleSend: () => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  hasFiles: boolean;
}

export const ChatInput = ({
  input,
  setInput,
  isLoading,
  handleSend,
  fileInputRef,
  handleFileSelect,
  hasFiles,
}: Props) => {
  const canSend = input.trim() || hasFiles;

  return (
    <div className="relative flex items-end gap-2 bg-zinc-100 border border-zinc-700 rounded-2xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-primary transition-colors">
      <input
        type="file"
        multiple
        ref={fileInputRef}
        onChange={handleFileSelect}
        className="hidden"
        accept=".pdf,.docx,.txt,.md,.mp3,.mp4,.wav"
      />

      <button
        onClick={() => fileInputRef.current?.click()}
        className="mb-1 p-2 rounded-xl text-zinc-500 hover:bg-zinc-200 hover:text-zinc-800 transition-colors shrink-0 cursor-pointer"
        title="Dodaj pliki"
      >
        <Paperclip size={20} />
      </button>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (canSend && !isLoading) handleSend();
          }
        }}
        placeholder="Ask a question or upload files..."
        className="w-full bg-transparent border-none placeholder:text-zinc-500 text-zinc-800 text-[15px] leading-relaxed focus:ring-0 focus:outline-none resize-none py-2 custom-scrollbar"
        rows={1}
        style={{ minHeight: "44px", maxHeight: "200px" }}
      />

      <button
        onClick={handleSend}
        disabled={isLoading || !canSend}
        className={`mb-1 p-2 rounded-xl flex items-center justify-center shrink-0 transition-all ${
          canSend
            ? "bg-zinc-900 text-white hover:bg-black shadow-lg cursor-pointer"
            : "bg-zinc-200 text-zinc-400 cursor-not-allowed"
        }`}
      >
        {canSend ? (
          <ArrowUp size={20} strokeWidth={2.5} />
        ) : (
          <Send size={20} strokeWidth={2} />
        )}
      </button>
    </div>
  );
};
