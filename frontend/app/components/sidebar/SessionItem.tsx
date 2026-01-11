import { MessageSquare, Edit2, Trash2, Check } from "lucide-react";
import { Session } from "../../../types";

interface Props {
  session: Session;
  isActive: boolean;
  isEditing: boolean;
  newTitle: string;
  setNewTitle: (t: string) => void;
  switchSession: (id: string) => void;
  startEditing: (e: React.MouseEvent, s: Session) => void;
  saveTitle: (e: React.FormEvent | React.KeyboardEvent, id: string) => void;
  confirmDelete: (e: React.MouseEvent, id: string) => void;
}

export const SessionItem = ({
  session,
  isActive,
  isEditing,
  newTitle,
  setNewTitle,
  switchSession,
  startEditing,
  saveTitle,
  confirmDelete,
}: Props) => {
  const sid = session.session_id || session._id || "";

  return (
    <div
      onClick={() => {
        if (sid) switchSession(sid);
      }}
      className={`group relative w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-all cursor-pointer truncate ${
        isActive
          ? "bg-zinc-800 text-white border-zinc-700 border"
          : "text-zinc-400 hover:text-white hover:bg-zinc-800"
      }`}
    >
      <MessageSquare
        size={16}
        className={
          isActive ? "text-primary" : "text-zinc-600 group-hover:text-primary"
        }
      />

      {isEditing ? (
        <input
          autoFocus
          className="bg-transparent border-b border-primary outline-none w-full text-white"
          value={newTitle || ""}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && sid) saveTitle(e, sid);
          }}
          onBlur={(e) => {
            if (sid) saveTitle(e, sid);
          }}
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="truncate pr-10">{session.title}</span>
      )}

      <div className="absolute right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-inherit pl-2">
        {!isEditing ? (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                startEditing(e, session);
              }}
              className="p-1 hover:text-primary transition-colors cursor-pointer"
            >
              <Edit2 size={14} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (sid) confirmDelete(e, sid);
              }}
              className="p-1 hover:text-red-400 transition-colors cursor-pointer"
            >
              <Trash2 size={14} />
            </button>
          </>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (sid) saveTitle(e, sid);
            }}
            className="p-1 hover:text-green-400 cursor-pointer"
          >
            <Check size={14} />
          </button>
        )}
      </div>
    </div>
  );
};
