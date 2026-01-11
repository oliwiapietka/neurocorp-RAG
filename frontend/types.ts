export interface Session {
  session_id: string;
  _id?: string;
  title: string;
  created_at: string;
  last_update?: string;
}

export interface SidebarProps {
  activeTab: "chat" | "admin";
  setActiveTab: (tab: "chat" | "admin") => void;
  sessions: Session[];
  currentSessionId: string | null;
  createNewChat: () => void;
  switchSession: (id: string) => void;
  editingSessionId: string | null;
  newTitle: string;
  setNewTitle: (t: string) => void;
  startEditing: (e: React.MouseEvent, s: Session) => void;
  saveTitle: (e: React.FormEvent | React.KeyboardEvent, id: string) => void;
  confirmDelete: (e: React.MouseEvent, id: string) => void;
}

export type AdminStatus = {
  type: "success" | "error" | "loading" | null;
  msg: string;
};

export interface ImageResult {
  uuid_name: string;
  original_doc: string;
  score: number;
  reason: "semantic_match" | "layout_relation";
}

export interface Citation {
  id: number;
  filename: string;
  uuid_name: string;
  page?: number;
  snippet: string;
  is_global: boolean;
  type: "db" | "web";
  url?: string;
}

export interface Message {
  role: "user" | "ai" | "system";
  content: string;
  timestamp?: string;
  citations?: Citation[];
  attachments?: string[];
  images?: ImageResult[];
}
