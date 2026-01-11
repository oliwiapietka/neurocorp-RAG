import { useState, useRef } from "react";
import { Message } from "../types";

const API_URL = "http://localhost:8000/api/v1";

export const useChat = (onFirstMessage: () => void) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isFilesExpanded, setIsFilesExpanded] = useState(false);
  const [viewingAttachments, setViewingAttachments] = useState<string[] | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(prev => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFiles([]);
  };

  const handleSend = async (activeSessionId: string) => {
    if (!input.trim() && selectedFiles.length === 0) return;
    
    const isFirst = messages.length === 0;
    const currentFiles = [...selectedFiles];
    const userMsg = input;

    setInput("");
    setSelectedFiles([]);
    setIsFilesExpanded(false);
    setMessages(prev => [...prev, { role: "user", content: userMsg, attachments: currentFiles.map(f => f.name) }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("message", userMsg);
      formData.append("session_id", activeSessionId);
      currentFiles.forEach(f => formData.append("files", f));

      const res = await fetch(`${API_URL}/chat/`, { method: "POST", body: formData });
      if (!res.ok) throw new Error();
      const data = await res.json();

      setMessages(prev => [...prev, { role: "ai", content: data.response, citations: data.citations, images: data.images }]);
      if (isFirst) onFirstMessage();
    } catch (e) { 
      console.error(e); 
    } finally { 
      setIsLoading(false); 
    }
  };

  const handleDownload = async (uuid: string, name: string) => {
    const link = document.createElement("a");
    link.href = `${API_URL}/sessions/download/${uuid}?original_name=${encodeURIComponent(name)}`;
    link.setAttribute("download", name);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return {
    messages, setMessages, input, setInput, isLoading, setIsLoading,
    selectedFiles, setSelectedFiles, isFilesExpanded, setIsFilesExpanded,
    viewingAttachments, setViewingAttachments, handleSend, handleDownload,
    fileInputRef, handleFileSelect, removeFile, clearAllFiles
  };
};