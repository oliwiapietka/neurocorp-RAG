import { useState } from "react";
import { AdminStatus } from "../types";

const API_URL = "http://localhost:8000/api/v1";

export const useAdmin = () => {
  const [adminFiles, setAdminFiles] = useState<File[]>([]);
  const [isAdminFilesExpanded, setIsAdminFilesExpanded] = useState(false);
  const [isClearingDatabase, setIsClearingDatabase] = useState(false);
  const [adminStatus, setAdminStatus] = useState<AdminStatus>({
    type: null,
    msg: "",
  });

  const handleAdminUpload = async () => {
    if (adminFiles.length === 0) return;

    setAdminStatus({
      type: "loading",
      msg: "Processing documents and creating vectors...",
    });

    const formData = new FormData();
    adminFiles.forEach((f) => formData.append("files", f));

    try {
      const res = await fetch(`${API_URL}/admin/ingest`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setAdminStatus({
          type: "success",
          msg: `Success! Indexed ${data.chunks_added} knowledge chunks.`,
        });
        setAdminFiles([]);
      } else {
        throw new Error(data.detail || "Server error");
      }
    } catch (e) {
      console.error("Ingestion error:", e);
      setAdminStatus({
        type: "error",
        msg: "Failed to add documents to the database.",
      });
    }
  };

  const handleActualClearDatabase = async () => {
    setIsClearingDatabase(false);
    setAdminStatus({ type: "loading", msg: "Clearing data from Qdrant..." });

    try {
      const res = await fetch(`${API_URL}/admin/clear`, {
        method: "DELETE",
      });

      if (res.ok) {
        setAdminStatus({
          type: "success",
          msg: "Knowledge base has been completely cleared.",
        });
      } else {
        throw new Error();
      }
    } catch (e) {
      setAdminStatus({
        type: "error",
        msg: "An error occurred while clearing the database.",
      });
    }
  };

  const removeAdminFile = (index: number) => {
    setAdminFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return {
    adminFiles,
    setAdminFiles,
    isAdminFilesExpanded,
    setIsAdminFilesExpanded,
    isClearingDatabase,
    setIsClearingDatabase,
    adminStatus,
    setAdminStatus,
    handleAdminUpload,
    handleActualClearDatabase,
    removeAdminFile,
  };
};
