import { Database } from "lucide-react";

export const AdminHeader = () => (
  <div className="flex items-center gap-3 mb-8 border-b border-zinc-800 pb-6">
    <div className="w-12 h-12 bg-zinc-900 rounded-xl flex items-center justify-center border border-zinc-800">
      <Database size={24} className="text-zinc-500" />
    </div>
    <div>
      <h1 className="text-2xl font-bold text-zinc-500">Knowledge Base</h1>
      <p className="text-zinc-600 text-sm">Manage Admin Knowledge Repository</p>
    </div>
  </div>
);
