import React from 'react';

/**
 * AuviLogo — Minimal scissors icon representing video clipping.
 * No background, just a clean black icon.
 */
export default function Logo({ size = 32, showWordmark = true, className = '' }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
        aria-hidden
      >
        {/* Top blade */}
        <circle cx="10" cy="9" r="3.5" className="stroke-text-primary" strokeWidth="2" fill="none" />
        <line x1="12.5" y1="11.5" x2="22" y2="20" className="stroke-text-primary" strokeWidth="2.2" strokeLinecap="round" />
        {/* Bottom blade */}
        <circle cx="10" cy="23" r="3.5" className="stroke-text-primary" strokeWidth="2" fill="none" />
        <line x1="12.5" y1="20.5" x2="22" y2="12" className="stroke-text-primary" strokeWidth="2.2" strokeLinecap="round" />
        {/* Film strip notches */}
        <rect x="24" y="11" width="3" height="3" rx="0.5" className="fill-text-primary" />
        <rect x="24" y="18" width="3" height="3" rx="0.5" className="fill-text-primary" />
      </svg>
      {showWordmark && (
        <span className="text-lg font-semibold tracking-tight text-text-primary">
          AUVI
        </span>
      )}
    </div>
  );
}



