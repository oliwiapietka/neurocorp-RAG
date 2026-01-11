"use client";
import { Settings } from "lucide-react";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarNav } from "./SidebarNav";
import { SessionItem } from "./SessionItem";
import { SidebarProps } from "../../../types";

export default function Sidebar(props: SidebarProps) {
  return (
    <aside className="w-[280px] bg-zinc-900 border-r border-zinc-800 flex flex-col hidden md:flex shrink-0">
      <SidebarHeader />

      <SidebarNav
        activeTab={props.activeTab}
        setActiveTab={props.setActiveTab}
        createNewChat={props.createNewChat}
      />

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-2">
          Chat History
        </div>
        {props.sessions.map((session) => (
          <SessionItem
            key={
              session.session_id || session._id || `session-${Math.random()}`
            }
            session={session}
            isActive={
              props.currentSessionId === session.session_id &&
              props.activeTab === "chat"
            }
            isEditing={props.editingSessionId === session.session_id}
            newTitle={props.newTitle}
            setNewTitle={props.setNewTitle}
            switchSession={props.switchSession}
            startEditing={props.startEditing}
            saveTitle={props.saveTitle}
            confirmDelete={props.confirmDelete}
          />
        ))}
      </div>

      <div className="mt-auto p-4 border-t border-zinc-800">
        <div className="flex items-center gap-3 text-sm text-zinc-500 hover:text-zinc-100 cursor-pointer transition-colors">
          <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
            <Settings size={16} />
          </div>
          <span>Settings</span>
        </div>
      </div>
    </aside>
  );
}
