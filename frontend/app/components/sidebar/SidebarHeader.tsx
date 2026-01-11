import { Sparkles } from "lucide-react";

export const SidebarHeader = () => (
  <div className="p-6 flex items-center gap-3 border-b border-zinc-800">
    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
      <Sparkles size={18} className="text-white" />
    </div>
    <span className="font-bold tracking-wide text-zinc-100">NeuroCorp</span>
  </div>
);
