import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Download, Copy, CheckCircle, Flame, Scissors, Clock, UploadCloud, Youtube } from 'lucide-react';
import useClipStore from '../store/useClipStore';

export default function ClipCard({ clip, index = 0 }) {
  const { openPreview } = useClipStore();
  const [copied, setCopied] = useState(false);
  const [localStatus, setLocalStatus] = useState(clip.approval_status || 'pending');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async (e) => {
    e.stopPropagation();
    setIsProcessing(true);
    try {
      await fetch(`http://localhost:8000/api/clips/${clip.id}/approve`, { method: 'POST' });
      setLocalStatus('approved');
    } catch (err) {
      console.error(err);
    }
    setIsProcessing(false);
  };

  const handleReject = async (e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this draft clip?")) return;
    
    setIsProcessing(true);
    try {
      await fetch(`http://localhost:8000/api/clips/${clip.id}/reject`, { method: 'POST' });
      setLocalStatus('rejected');
      // If we are in Dashboard, it might be good to remove it from state, but for now setting local status to 'rejected' hides it or dims it.
    } catch (err) {
      console.error(err);
      setIsProcessing(false);
    }
  };

  const getScoreGradient = (score) => {
    if (score >= 70) return 'from-fuchsia-500 to-orange-400';
    if (score >= 40) return 'from-violet-500 to-fuchsia-500';
    return 'from-zinc-500 to-zinc-400';
  };

  const getScoreLabel = (score) => {
    if (score >= 70) return 'Very high';
    if (score >= 40) return 'Solid';
    return 'Moderate';
  };

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleCopyLink = (e) => {
    e.stopPropagation();
    const url = `${window.location.origin}${window.location.pathname}?t=${clip.start}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (e) => {
    e.stopPropagation();
    if (clip.download_url) {
      const a = document.createElement('a');
      a.href = clip.download_url;
      a.download = `clip_${clip.index}.mp4`; // Fallback, the header handles the real filename
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  if (localStatus === 'rejected') {
    return null; // Hide rejected/deleted clips
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all hover:shadow-md hover:border-accent-1/40"
    >
      {/* Vertical 9:16 preview with real thumbnail */}
      <div className="relative mx-auto mt-3 w-full max-w-[200px]">
        <div
          className="relative aspect-[9/16] w-full overflow-hidden rounded-xl border border-border cursor-pointer bg-black"
          onClick={() => openPreview(clip)}
        >
          {clip.thumbnail_url ? (
            <img
              src={clip.thumbnail_url}
              alt={clip.title}
              className="absolute inset-0 h-full w-full object-cover opacity-90 transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 bg-slate-100 opacity-30" />
          )}

          {/* Score badge */}
          <div className="absolute left-2 top-2">
            <div
              className={`grid size-9 place-items-center rounded-full text-xs font-bold text-white shadow-lg ${getScoreGradient(clip.score)}`}
            >
              {clip.score}
            </div>
          </div>

          {/* Category chip */}
          {clip.category && (
            <div className="absolute right-2 top-2">
              <span className="rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-white backdrop-blur">
                {clip.category}
              </span>
            </div>
          )}

          {/* Play overlay */}
          <div className="absolute inset-0 grid place-items-center bg-black/30 opacity-0 transition-opacity group-hover:opacity-100 backdrop-blur-[2px]">
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); openPreview(clip); }}
              className="grid size-12 place-items-center rounded-full bg-white/15 backdrop-blur-md transition-transform hover:scale-110"
              aria-label="Preview clip"
            >
              <Play className="w-5 h-5 translate-x-0.5 fill-white text-white" />
            </button>
          </div>

          {/* Duration */}
          <div className="absolute bottom-2 right-2 rounded bg-black/50 px-1.5 py-0.5 text-[9px] font-mono text-white backdrop-blur">
            {formatDuration(clip.duration)}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-accent-1">
            <Flame className="w-3 h-3" />
            {getScoreLabel(clip.score)} virality
          </div>
          <h3
            className="line-clamp-2 text-sm font-semibold leading-snug group-hover:text-accent-1 text-text-primary transition-colors"
            title={clip.title}
          >
            {clip.title}
          </h3>
        </div>

        {/* Source timestamp */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-text-muted">
          <span className="flex items-center gap-1">
            <Scissors className="w-3 h-3" />
            {formatTimestamp(clip.start)} → {formatTimestamp(clip.end)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDuration(clip.duration)}
          </span>
        </div>

        {/* Score meter */}
        <div className="flex items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-border">
            <div
              className={`h-full ${getScoreGradient(clip.score)}`}
              style={{ width: `${clip.score}%` }}
            />
          </div>
          <span className="text-[11px] font-mono font-semibold text-text-primary">{clip.score}</span>
        </div>

        {/* Actions */}
        {localStatus === 'published' ? (
          <div className="mt-auto flex items-center gap-2 pt-2">
            <a 
              href={clip.published_url || '#'} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex-1 btn-primary py-2 px-3 text-sm shadow-none gap-1.5 bg-red-600 hover:bg-red-700 text-white"
            >
              <Youtube className="w-4 h-4" />
              View on YouTube
            </a>
          </div>
        ) : (
          <div className="mt-auto flex items-center gap-1.5 pt-2">
            <button
              onClick={() => openPreview(clip)}
              className="flex-1 btn-primary py-2 px-3 text-sm shadow-none gap-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            
            {localStatus === 'pending' || localStatus === 'rejected' ? (
              <button
                onClick={handleApprove}
                disabled={isProcessing}
                className="btn-secondary py-2 px-3 hover:text-green-600 hover:border-green-600 transition-colors bg-green-500/10 text-green-600 border-green-500/20"
                title="Approve & Upload to YouTube"
              >
                {isProcessing ? <div className="w-4 h-4 animate-spin rounded-full border-2 border-green-600 border-t-transparent" /> : <UploadCloud className="w-4 h-4" />}
              </button>
            ) : (
              <div className="py-2 px-3 flex items-center gap-1 text-xs font-medium text-amber-500 bg-amber-500/10 rounded border border-amber-500/20">
                <div className="w-3 h-3 animate-pulse rounded-full bg-amber-500" />
                Uploading...
              </div>
            )}
            
            <button
              onClick={handleDownload}
              className="btn-secondary py-2 px-3 hover:text-slate-900 hover:border-slate-900 transition-colors"
              title="Download MP4"
              aria-label="Download"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="btn-secondary py-2 px-3 hover:text-red-600 hover:border-red-600 transition-colors"
              title="Delete Draft"
              aria-label="Delete"
            >
              <svg xmlns="http://www.w3.org/2005/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
            </button>
            <button
              onClick={handleCopyLink}
              className="btn-secondary py-2 px-3 hover:text-slate-900 transition-colors relative"
              title="Copy Timestamp Link"
              aria-label="Copy link"
            >
              {copied ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
