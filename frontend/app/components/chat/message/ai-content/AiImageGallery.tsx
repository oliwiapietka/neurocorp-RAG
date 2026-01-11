import { motion } from "framer-motion";
import { Sparkles, Maximize2, FileText } from "lucide-react";
import { ImageResult } from "../../../../../types";

export const AiImageGallery = ({ images }: { images?: ImageResult[] }) => {
  if (!images || images.length === 0) return null;

  return (
    <div className="mt-4 mb-2 space-y-3">
      {/* Nagłówek sekcji - czystszy i bardziej profesjonalny */}
      <div className="flex items-center gap-1 px-1">
        <div className="p-1 bg-zinc-100 rounded-md">
          <Sparkles size={12} className="text-zinc-500" />
        </div>
        <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-zinc-500">
          Visual Document Analysis
        </span>
      </div>

      {/* Img grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {images.map((img, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -4 }}
            className="group relative flex flex-col bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md hover:border-zinc-300 transition-all cursor-zoom-in"
            onClick={() =>
              window.open(
                `http://localhost:8000/api/v1/sessions/download/${img.uuid_name}`,
                "_blank"
              )
            }
          >
            {/* Img container */}
            <div className="relative aspect-square overflow-hidden bg-zinc-50 border-b border-zinc-100">
              <img
                src={`http://localhost:8000/api/v1/sessions/download/${img.uuid_name}`}
                alt={img.original_doc}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                loading="lazy"
              />

              {/* Overlay when hovering */}
              <div className="absolute inset-0 bg-zinc-900/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div className="bg-white/90 backdrop-blur-md p-2 rounded-full shadow-lg transform scale-75 group-hover:scale-100 transition-transform">
                  <Maximize2 size={16} className="text-zinc-900" />
                </div>
              </div>
            </div>

            {/* Caption */}
            <div className="p-2 bg-white flex items-center gap-2">
              <FileText size={10} className="text-zinc-400 shrink-0" />
              <p className="text-[10px] font-bold text-zinc-600 truncate leading-tight uppercase tracking-tight">
                {img.original_doc.replace(/\.[^/.]+$/, "")}{" "}
              </p>
            </div>

            <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded text-[8px] font-black text-white opacity-0 group-hover:opacity-100 transition-opacity">
              AI MATCH: {(img.score * 100).toFixed(0)}%
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
