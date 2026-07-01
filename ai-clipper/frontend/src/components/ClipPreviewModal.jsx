import React, { useState, useRef, useEffect } from 'react';
import { X, Download, Play, Pause, ExternalLink } from 'lucide-react';
import useClipStore from '../store/useClipStore';
import VideoPlayer from './VideoPlayer';

export default function ClipPreviewModal() {
  const { previewOpen, selectedClip, closePreview } = useClipStore();
  const [currentTime, setCurrentTime] = useState(0);
  const playerRef = useRef(null);

  // Reset time when a new clip is selected
  useEffect(() => {
    if (previewOpen && selectedClip) {
      setCurrentTime(0);
    }
  }, [previewOpen, selectedClip]);

  if (!previewOpen || !selectedClip) return null;

  const handleTimeUpdate = (time) => {
    setCurrentTime(time);
    
    // Auto-loop when reaching the end of the clip duration
    if (time >= selectedClip.duration - 0.1) {
      if (playerRef.current) {
        playerRef.current.seekTo(0);
        playerRef.current.play();
      }
    }
  };

  const handleDownload = () => {
    if (selectedClip.download_url) {
      const a = document.createElement('a');
      a.href = selectedClip.download_url;
      a.download = `clip_${selectedClip.index}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const formatTime = (timeInSeconds) => {
    const m = Math.floor(timeInSeconds / 60);
    const s = Math.floor(timeInSeconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      {/* Dark Overlay backdrop-blur */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-md animate-fade-in"
        onClick={closePreview}
      ></div>
      
      {/* Modal Content */}
      <div className="relative w-full max-w-5xl auvi-gradient-card border border-border rounded-2xl auvi-glow overflow-hidden flex flex-col animate-slide-up max-h-[90vh]">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border bg-card/60 backdrop-blur">
          <div>
            <h2 className="text-lg font-semibold text-text-primary line-clamp-1">{selectedClip.title}</h2>
            <div className="flex items-center gap-3 mt-1">
              <span className="badge badge-accent">{selectedClip.category}</span>
              <span className="text-xs text-text-muted">
                Original Timeline: {formatTime(selectedClip.start)} - {formatTime(selectedClip.end)}
              </span>
            </div>
          </div>

          <button
            onClick={closePreview}
            className="p-2 rounded-lg hover:bg-card text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Main Body - Video Player */}
        <div className="relative w-full bg-black flex-grow flex items-center justify-center overflow-hidden min-h-[40vh] sm:min-h-[60vh]">
          {/* Use stream_url for playback (supports Range seeking), download_url as fallback */}
          {(selectedClip.stream_url || selectedClip.download_url) ? (
            <>
              <VideoPlayer 
                ref={playerRef}
                src={selectedClip.stream_url || selectedClip.download_url} 
                poster={selectedClip.thumbnail_url}
                onTimeUpdate={handleTimeUpdate}
                autoPlay={true}
              />
            </>
          ) : (
            <div className="text-center p-8">
              <p className="text-text-muted mb-2">Video preview not available</p>
              <p className="text-sm text-text-hint">Missing clip file path</p>
            </div>
          )}
        </div>
        
        {/* Footer Controls */}
        <div className="p-4 bg-card/60 backdrop-blur border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-sm text-text-muted mb-1">Viral Score</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-surface rounded-full overflow-hidden border border-border">
                  <div
                    className="h-full auvi-gradient-brand"
                    style={{ width: `${selectedClip.score}%` }}
                  ></div>
                </div>
                <span className="text-sm font-bold text-text-primary">{selectedClip.score}%</span>
              </div>
            </div>

            <div className="h-8 w-px bg-border mx-2"></div>

            <div className="flex flex-col">
              <span className="text-sm text-text-muted mb-1">Duration</span>
              <span className="text-sm font-bold text-text-primary">{selectedClip.duration.toFixed(1)}s</span>
            </div>
          </div>

          <button
            onClick={handleDownload}
            className="btn-primary"
          >
            <Download className="w-4 h-4" />
            <span>Download MP4</span>
          </button>
        </div>
        
      </div>
    </div>
  );
}
