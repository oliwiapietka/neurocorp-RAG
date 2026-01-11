import { Trash2 } from "lucide-react";

export const AdminDangerZone = ({ onClear }: { onClear: () => void }) => (
  <section className="mt-12">
    <div className="bg-red-950/20 border border-red-900/50 rounded-2xl p-6 flex items-center justify-between">
      <div>
        <h3 className="font-medium text-red-900">Clear Knowledge Base</h3>
        <p className="text-sm text-red-900/50 mt-1">
          This action will purge all records from the Qdrant vector store.
        </p>
      </div>
      <button
        onClick={onClear}
        className="px-4 py-2 bg-red-900/85 hover:bg-red-900 text-red-200 rounded-lg border border-red-800 transition-colors flex items-center gap-2 text-sm cursor-pointer"
      >
        <Trash2 size={16} /> Clear
      </button>
    </div>
  </section>
);
