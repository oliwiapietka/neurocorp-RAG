import { useState, useEffect } from "react";
import { Session } from "../types";
import { v4 as uuidv4 } from "uuid";

const API_URL = "http://localhost:8000/api/v1";

export const useSessions = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_URL}/sessions/`);
      if (res.ok) setSessions(await res.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchSessions(); }, []);

  const switchSession = (id: string) => setCurrentSessionId(id);

  const startEditing = (e: React.MouseEvent, session: Session) => {
    e.stopPropagation();
    setEditingSessionId(session.session_id);
    setNewTitle(session.title);
  };

  const confirmDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletingSessionId(id);
  };

  const saveTitle = async (e: any, sessionId: string) => {
    if (e) e.stopPropagation();
    if (!newTitle.trim()) { setEditingSessionId(null); return; }
    try {
      const res = await fetch(`${API_URL}/sessions/${sessionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });
      if (res.ok) {
        setSessions(prev => prev.map(s => s.session_id === sessionId ? { ...s, title: newTitle } : s));
        setEditingSessionId(null);
      }
    } catch (e) { console.error(e); }
  };

  const handleActualDelete = async () => {
    if (!deletingSessionId) return;
    try {
      const res = await fetch(`${API_URL}/sessions/${deletingSessionId}`, { method: "DELETE" });
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.session_id !== deletingSessionId));
        if (currentSessionId === deletingSessionId) setCurrentSessionId(null);
      }
    } finally { setDeletingSessionId(null); }
  };

  const createNewChat = async () => {
    const newId = uuidv4();
    const res = await fetch(`${API_URL}/sessions/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: newId, title: "New Chat" }),
    });
    if (res.ok) {
      const newS = await res.json();
      setSessions(prev => [newS, ...prev]);
      setCurrentSessionId(newS.session_id);
      return newS;
    }
  };

  return {
    sessions, currentSessionId, editingSessionId, newTitle, deletingSessionId,
    setCurrentSessionId, setEditingSessionId, setNewTitle, setDeletingSessionId,
    fetchSessions, createNewChat, saveTitle, switchSession, startEditing, confirmDelete, handleActualDelete
  };
};