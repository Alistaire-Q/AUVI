import React, { useState, useRef } from 'react';

export default function ClipTimeline({ clips, duration, currentTime, onSeek }) {
  const [hoveredClip, setHoveredClip] = useState(null);
  const [hoverX, setHoverX] = useState(0);
  const containerRef = useRef(null);

  if (!duration || duration <= 0) return null;

  const handleMouseMove = (e, clip) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setHoverX(e.clientX - rect.left);
    setHoveredClip(clip);
  };

  const handleMouseLeave = () => {
    setHoveredClip(null);
  };

  const getClipColor = (score) => {
    if (score >= 70) return 'bg-success hover:bg-success/80';
    if (score >= 40) return 'bg-warning hover:bg-warning/80';
    return 'bg-danger hover:bg-danger/80';
  };

  return (
    <div className="relative w-full h-8 mt-2" ref={containerRef}>
      {/* Base Timeline Track */}
      <div className="absolute top-1/2 left-0 right-0 h-2 -translate-y-1/2 bg-surface rounded-full border border-border overflow-hidden">
        {/* Current Time Indicator (background progress) */}
        <div 
          className="absolute top-0 bottom-0 left-0 bg-white/10"
          style={{ width: `${(currentTime / duration) * 100}%` }}
        />
      </div>

      {/* Clip Segments */}
      {clips.map((clip) => {
        const leftPercent = (clip.start / duration) * 100;
        const widthPercent = (clip.duration / duration) * 100;
        
        return (
          <div
            key={clip.id}
            className={`absolute top-1/2 h-3 -translate-y-1/2 rounded-sm cursor-pointer transition-colors z-10 ${getClipColor(clip.score)}`}
            style={{ 
              left: `${leftPercent}%`, 
              width: `${Math.max(widthPercent, 0.5)}%` // Ensure at least tiny visible width
            }}
            onMouseMove={(e) => handleMouseMove(e, clip)}
            onMouseLeave={handleMouseLeave}
            onClick={() => onSeek(clip.start)}
          />
        );
      })}

      {/* Current Time Playhead */}
      <div 
        className="absolute top-1 bottom-1 w-[2px] bg-white z-20 pointer-events-none transition-all duration-100 ease-linear shadow-[0_0_5px_rgba(255,255,255,0.8)]"
        style={{ left: `${(currentTime / duration) * 100}%` }}
      />

      {/* Hover Tooltip */}
      {hoveredClip && (
        <div 
          className="absolute bottom-full mb-2 bg-card border border-border rounded-lg shadow-xl p-2 w-48 z-50 pointer-events-none transform -translate-x-1/2 animate-fade-in"
          style={{ left: `${hoverX}px` }}
        >
          {hoveredClip.thumbnail_url && (
            <img 
              src={hoveredClip.thumbnail_url} 
              alt="Thumbnail" 
              className="w-full aspect-video object-cover rounded mb-2 border border-border/50"
            />
          )}
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-semibold text-text-primary">
              Score: {hoveredClip.score}
            </span>
            <span className="text-[10px] text-text-muted">
              {hoveredClip.duration.toFixed(1)}s
            </span>
          </div>
          <p className="text-[10px] text-text-muted line-clamp-2">
            {hoveredClip.title}
          </p>
        </div>
      )}
    </div>
  );
}
