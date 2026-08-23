import React from 'react';

/**
 * AuviLogo — Minimalist black & white brand mark.
 * A play triangle split by a vertical cut, representing video clipping.
 */
export default function Logo({ size = 32, showWordmark = true, className = '' }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
        aria-hidden
      >
        {/* Rounded square background */}
        <rect width="32" height="32" rx="8" className="fill-text-primary" />
        {/* Play triangle — left half */}
        <path d="M11 8 L11 24 L16 20.8" fill="white" />
        {/* Play triangle — right half (offset slightly to show the cut) */}
        <path d="M17 19.2 L23 16 L17 12.8" fill="white" />
        {/* Cut line */}
        <line x1="16.5" y1="7" x2="16.5" y2="25" stroke="white" strokeWidth="0.8" strokeDasharray="1.5 1.5" opacity="0.5" />
      </svg>
      {showWordmark && (
        <span className="text-lg font-semibold tracking-tight text-text-primary">
          AUVI
        </span>
      )}
    </div>
  );
}


