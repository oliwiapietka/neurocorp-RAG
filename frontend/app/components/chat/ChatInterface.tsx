"use client";
import {
  Bot,
  User,
  Sparkles,
  FileText,
  Search,
  PenTool,
  Lightbulb,
  Loader2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Message } from "../../../types";
import { AiResponse } from "./message/ai-content/AiResponse";
import { UserMessage } from "./message/UserMessage";
import { AttachmentList } from "./message/AttachmentList";
import { FilePreview } from "./input/FilePreview";
import { ChatInput } from "./input/ChatInput";
import { AiThinking } from "./message/ai-content/AiThinking";

interface ChatProps {
  messages: Message[];
  input: string;
  setInput: (v: string) => void;
  isLoading: boolean;
  handleSend: () => void;
  selectedFiles: File[];
  isFilesExpanded: boolean;
  setIsFilesExpanded: (v: boolean) => void;
  clearAllFiles: (e: React.MouseEvent) => void;
  removeFile: (i: number) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  setViewingAttachments: (f: string[] | null) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  getFileIcon: (n: string) => React.ReactNode;
  handleDownload: (uuidFilename: string, originalName: string) => Promise<void>;
}

export default function ChatInterface(props: ChatProps) {
  const starterQuestions = [
    {
      icon: <FileText size={18} />,
      label: "Create a summary",
      text: "Write a brief summary of the latest project findings.",
    },
    {
      icon: <Search size={18} />,
      label: "Search knowledge base",
      text: "Find information regarding the company's safety procedures.",
    },
    {
      icon: <PenTool size={18} />,
      label: "Draft an email",
      text: "Help me write a formal email to a client regarding a delay.",
    },
    {
      icon: <Lightbulb size={18} />,
      label: "Brainstorm ideas",
      text: "Suggest 5 creative ideas for a marketing campaign.",
    },
  ];

  const renderContent = () => {
    if (props.isLoading && props.messages.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center h-full text-zinc-400 gap-3">
          <Loader2 size={32} className="animate-spin text-emerald-500" />
          <p className="text-sm font-medium animate-pulse">
            Loading conversation...
          </p>
        </div>
      );
    }

    if (props.messages.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in duration-500 slide-in-from-bottom-5">
          <div className="w-24 h-24 bg-gradient-to-tr from-emerald-50 to-zinc-100 rounded-[2rem] flex items-center justify-center shadow-sm border border-zinc-100 mb-8">
            <Bot
              size={48}
              className="text-emerald-600 drop-shadow-sm"
              strokeWidth={1.5}
            />
          </div>
          <h1 className="text-2xl md:text-3xl font-semibold text-zinc-800 mb-3 text-center tracking-tight">
            How can I help you today?
          </h1>
          <p className="text-zinc-500 text-center max-w-md mb-12 leading-relaxed">
            I have access to the corporate knowledge base and can help you
            analyze documents and data.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
            {starterQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => props.setInput(q.text)}
                className="flex items-center gap-4 p-4 rounded-xl border border-zinc-200 bg-white hover:border-emerald-500/50 hover:shadow-md hover:shadow-emerald-500/5 transition-all group text-left cursor-pointer"
              >
                <div className="w-10 h-10 rounded-lg bg-zinc-50 border border-zinc-100 flex items-center justify-center text-zinc-500 group-hover:text-emerald-600 group-hover:bg-emerald-50 transition-colors">
                  {q.icon}
                </div>
                <div>
                  <div className="text-sm font-medium text-zinc-700 group-hover:text-zinc-900">
                    {q.label}
                  </div>
                  <div className="text-xs text-zinc-400 mt-0.5 group-hover:text-zinc-500">
                    Click to start
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      );
    }

    return (
      <>
        <AnimatePresence initial={false}>
          {props.messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "ai" && (
                <div className="w-8 h-8 rounded-full bg-white border border-zinc-300 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                  <Bot size={16} className="text-zinc-600" />
                </div>
              )}

              <div className="flex flex-col gap-1 max-w-[85%] md:max-w-[75%]">
                <AttachmentList
                  files={msg.attachments || []}
                  isUser={msg.role === "user"}
                  getFileIcon={props.getFileIcon}
                  setViewingAttachments={props.setViewingAttachments}
                />

                {msg.role === "user" ? (
                  <UserMessage content={msg.content} />
                ) : (
                  <AiResponse msg={msg} handleDownload={props.handleDownload} />
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-white border border-zinc-300 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                  <User size={16} className="text-zinc-600" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {props.isLoading && props.messages.length > 0 && <AiThinking />}

        <div ref={props.messagesEndRef} className="h-4 flex-shrink-0" />
      </>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="h-14 border-b border-zinc-200 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 block"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 block absolute top-0 animate-ping opacity-40"></span>
          </div>
          <span className="text-sm font-semibold text-zinc-900 tracking-tight">
            NeuroCorp <span className="text-zinc-400 font-normal mx-1">/</span>{" "}
            Intelligence Engine
          </span>
        </div>
        <div className="flex items-center gap-2 bg-zinc-100 px-3 py-1 rounded-full border border-zinc-200">
          <span className="text-[10px] font-black text-zinc-500 uppercase tracking-tighter">
            Model
          </span>
          <span className="text-[10px] font-bold text-zinc-900 uppercase">
            Llama 3.3
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
        <div className="max-w-3xl mx-auto py-8 space-y-8 h-full flex flex-col">
          {renderContent()}
        </div>
      </div>

      <div className="p-4 md:p-6 bg-background border-t border-zinc-800">
        <div className="max-w-3xl mx-auto relative flex flex-col gap-2">
          <FilePreview
            selectedFiles={props.selectedFiles}
            isExpanded={props.isFilesExpanded}
            setIsExpanded={props.setIsFilesExpanded}
            removeFile={props.removeFile}
            clearAll={props.clearAllFiles}
            getFileIcon={props.getFileIcon}
          />
          <ChatInput
            input={props.input}
            setInput={props.setInput}
            isLoading={props.isLoading}
            handleSend={props.handleSend}
            fileInputRef={props.fileInputRef}
            handleFileSelect={props.handleFileSelect}
            hasFiles={props.selectedFiles.length > 0}
          />
          <p className="text-center text-[10px] text-zinc-500 mt-2 uppercase tracking-[0.2em] font-bold opacity-50">
            NeuroCorp - Intelligence Multimodal RAG Engine
          </p>
        </div>
      </div>
    </div>
  );
}
