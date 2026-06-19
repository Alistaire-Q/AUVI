import React, { useState } from 'react';
import { Play, Download, Copy, CheckCircle } from 'lucide-react';
import useClipStore from '../store/useClipStore';

export default function ClipCard({ clip }) {
  const { openPreview } = useClipStore();
  const [copied, setCopied] = useState(false);

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-success bg-success/10 border-success/30';
    if (score >= 40) return 'text-warning bg-warning/10 border-warning/30';
    return 'text-danger bg-danger/10 border-danger/30';
  };

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleCopyLink = () => {
    const url = `${window.location.origin}${window.location.pathname}?t=${clip.start}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    // Initiate download
    if (clip.download_url) {
      const a = document.createElement('a');
      a.href = clip.download_url;
      a.download = `clip_${clip.index}.mp4`; // Fallback, the header handles the real filename
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  return (
    <div className="card overflow-hidden group flex flex-col h-full">
      {/* Thumbnail Container */}
      <div className="relative aspect-video bg-black overflow-hidden border-b border-border">
        {clip.thumbnail_url ? (
          <img 
            src={clip.thumbnail_url} 
            alt={clip.title} 
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 opacity-80 group-hover:opacity-100"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-surface">
            <span className="text-text-muted">No Thumbnail</span>
          </div>
        )}
        
        {/* Play Overlay */}
        <div 
          className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer backdrop-blur-[2px]"
          onClick={() => openPreview(clip)}
        >
          <div className="w-12 h-12 rounded-full bg-accent-1/90 text-white flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.6)] transform scale-90 group-hover:scale-100 transition-transform">
            <Play className="w-6 h-6 ml-1" />
          </div>
        </div>

        {/* Duration Badge */}
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 text-white text-xs font-medium rounded backdrop-blur-sm border border-white/10">
          {formatDuration(clip.duration)}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-grow">
        <div className="flex justify-between items-start mb-2 gap-2">
          {/* Category Tag */}
          <span className="badge badge-accent shrink-0">
            {clip.category}
          </span>
          
          {/* Viral Score */}
          <div className={`px-2 py-1 rounded text-xs font-bold border flex items-center gap-1 ${getScoreColor(clip.score)}`}>
            <span>Score:</span>
            <span className="text-sm">{clip.score}</span>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-text-primary font-semibold text-sm line-clamp-2 mb-4 flex-grow group-hover:text-accent-1 transition-colors" title={clip.title}>
          {clip.title}
        </h3>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-auto pt-3 border-t border-border">
          <button 
            onClick={() => openPreview(clip)}
            className="flex-1 btn-primary py-2 px-3 text-sm shadow-none"
          >
            <Play className="w-4 h-4" />
            <span>Preview</span>
          </button>
          
          <button 
            onClick={handleDownload}
            className="btn-secondary py-2 px-3 hover:text-accent-1 hover:border-accent-1 transition-colors"
            title="Download MP4"
          >
            <Download className="w-4 h-4" />
          </button>

          <button 
            onClick={handleCopyLink}
            className="btn-secondary py-2 px-3 hover:text-white transition-colors relative"
            title="Copy Timestamp Link"
          >
            {copied ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
