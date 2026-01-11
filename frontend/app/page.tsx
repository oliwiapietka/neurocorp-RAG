"use client";
import React, { useState, useRef, useEffect, ReactNode } from "react";
import Sidebar from "./components/sidebar/Sidebar";
import ChatInterface from "./components/chat/ChatInterface";
import AdminPanel from "./components/admin/AdminPanel";
import Modals from "./components/modals/Modals";

import { useSessions } from "../hooks/useSessions";
import { useChat } from "../hooks/useChat";
import { useAdmin } from "../hooks/useAdmin";
import { FileAudio, FileVideo, FileText } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "admin">("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const adminFileInputRef = useRef<HTMLInputElement>(null);

  const sessions = useSessions();
  const chat = useChat(sessions.fetchSessions);
  const admin = useAdmin();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat.messages, chat.isLoading]);

  const handleSwitchSession = async (id: string) => {
    if (id === sessions.currentSessionId) return;
    sessions.switchSession(id);
    setActiveTab("chat");

    chat.setMessages([]);
    chat.setIsLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/sessions/${id}`);
      if (res.ok) {
        const data = await res.json();
        chat.setMessages(data.messages || []);
      }
    } finally {
      chat.setIsLoading(false);
    }
  };

  const handleCreateNewChat = async () => {
    await sessions.createNewChat();
    chat.setMessages([]);
    chat.setIsLoading(false);
    setActiveTab("chat");
  };

  const getFileIcon = (name: string): ReactNode => {
    if (name.match(/\.(mp3|wav)$/i))
      return <FileAudio size={16} className="text-purple-500" />;
    if (name.match(/\.(mp4)$/i))
      return <FileVideo size={16} className="text-blue-500" />;
    return <FileText size={16} className="text-zinc-500" />;
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      <Sidebar
        {...sessions}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        switchSession={handleSwitchSession}
        createNewChat={handleCreateNewChat}
      />

      <main className="flex-1 flex flex-col relative bg-background">
        {activeTab === "chat" ? (
          <ChatInterface
            {...chat}
            messages={chat.messages || []}
            handleSend={() => {
              if (sessions.currentSessionId)
                chat.handleSend(sessions.currentSessionId);
              else
                sessions
                  .createNewChat()
                  .then((s) => s && chat.handleSend(s.session_id));
            }}
            messagesEndRef={messagesEndRef}
            getFileIcon={getFileIcon}
          />
        ) : (
          <AdminPanel
            {...admin}
            handleAdminFileSelect={(e: any) =>
              e.target.files && admin.setAdminFiles(Array.from(e.target.files))
            }
            adminFileInputRef={adminFileInputRef}
          />
        )}

        <Modals {...sessions} {...chat} {...admin} getFileIcon={getFileIcon} />
      </main>
    </div>
  );
}
