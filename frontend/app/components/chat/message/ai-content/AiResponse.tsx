import { useMemo } from "react";
import { Message } from "../../../../../types";
import { AiMarkdown } from "./AiMarkdown";
import { AiImageGallery } from "./AiImageGallery";
import { AiSourceFooter } from "./AiSourceFooter";

interface Props {
  msg: Message;
  handleDownload: (uuid: string, name: string) => Promise<void>;
}

export const AiResponse = ({ msg, handleDownload }: Props) => {
  const { fileToIdMap, idToDisplayId } = useMemo(() => {
    const fMap = new Map<string, number>();
    const iMap: Record<number, number> = {};
    let nextId = 1;

    msg.citations?.forEach((c) => {
      if (!fMap.has(c.uuid_name)) fMap.set(c.uuid_name, nextId++);
      iMap[c.id] = fMap.get(c.uuid_name)!;
    });
    return { fileToIdMap: fMap, idToDisplayId: iMap };
  }, [msg.citations]);

  return (
    <div className="flex flex-col gap-4 w-full">
      <AiMarkdown
        content={msg.content}
        citations={msg.citations || []}
        idMap={idToDisplayId}
        onDownload={handleDownload}
      />
      <AiImageGallery images={msg.images} />
      <AiSourceFooter
        citations={msg.citations || []}
        fileToIdMap={fileToIdMap}
        content={msg.content}
        onDownload={handleDownload}
      />
    </div>
  );
};
