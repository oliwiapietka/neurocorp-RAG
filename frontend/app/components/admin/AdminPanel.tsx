"use client";
import { AdminHeader } from "./AdminHeader";
import { AdminUploadZone } from "./AdminUploadZone";
import { AdminDangerZone } from "./AdminDangerZone";
import { AdminStatusToast } from "./AdminStatusToast";
import { AdminStatus } from "../../../types";

interface AdminProps {
  adminFiles: File[];
  isAdminFilesExpanded: boolean;
  setIsAdminFilesExpanded: (v: boolean) => void;
  setAdminFiles: (f: File[]) => void;
  removeAdminFile: (i: number) => void;
  handleAdminUpload: () => void;
  handleAdminFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  adminFileInputRef: React.RefObject<HTMLInputElement | null>;
  setIsClearingDatabase: (v: boolean) => void;
  adminStatus: AdminStatus;
  setAdminStatus: (s: AdminStatus) => void;
}

export default function AdminPanel(props: AdminProps) {
  return (
    <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
      <div className="max-w-2xl mx-auto py-10">
        <AdminHeader />

        <AdminUploadZone
          adminFiles={props.adminFiles}
          isExpanded={props.isAdminFilesExpanded}
          setIsExpanded={props.setIsAdminFilesExpanded}
          setAdminFiles={props.setAdminFiles}
          removeFile={props.removeAdminFile}
          onUpload={props.handleAdminUpload}
          onFileSelect={props.handleAdminFileSelect}
          fileInputRef={props.adminFileInputRef}
        />

        <AdminDangerZone onClear={() => props.setIsClearingDatabase(true)} />

        <AdminStatusToast
          status={props.adminStatus}
          onClose={() => props.setAdminStatus({ type: null, msg: "" })}
        />
      </div>
    </div>
  );
}
