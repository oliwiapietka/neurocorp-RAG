import { Database, Plus } from "lucide-react";

interface Props {
  activeTab: "chat" | "admin";
  setActiveTab: (tab: "chat" | "admin") => void;
  createNewChat: () => void;
}

export const SidebarNav = ({
  activeTab,
  setActiveTab,
  createNewChat,
}: Props) => (
  <div className="p-3 pb-0 flex flex-col gap-1">
    <button
      onClick={() => setActiveTab("admin")}
      className={`w-full flex items-center gap-3 px-3 py-2.5 mb-1 text-sm font-medium rounded-lg transition-colors cursor-pointer border border-transparent ${
        activeTab === "admin"
          ? "bg-zinc-800 text-white border-zinc-700"
          : "text-zinc-400 hover:text-white hover:bg-zinc-800"
      }`}
    >
      <Database size={18} /> Knowledge Base
    </button>

    <button
      onClick={createNewChat}
      className="w-full flex items-center gap-3 px-3 py-2.5 mb-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors cursor-pointer border border-zinc-800 hover:border-zinc-700"
    >
      <Plus size={18} /> New Chat
    </button>
  </div>
);
