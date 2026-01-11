import ReactMarkdown from "react-markdown";

export const UserMessage = ({ content }: { content: string }) => (
  <div className="bg-white text-zinc-900 border border-zinc-300 px-5 py-2 rounded-2xl rounded-tr-sm font-medium text-left">
    <div className="prose prose-sm max-w-none prose-zinc">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  </div>
);
