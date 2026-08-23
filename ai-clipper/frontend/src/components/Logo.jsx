import React from 'react';

/**
 * AuviLogo — Play triangle cleanly split into two halves.
 * Represents video clipping through pure geometry. No background.
 */
export default function Logo({ size = 32, showWordmark = true, className = '' }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
        aria-hidden
      >
        {/* Left half — trapezoid slice of the play triangle */}
        <path
          d="M3.5 2.5 L3.5 21.5 L10.75 17 L10.75 7 Z"
          className="fill-text-primary"
        />
        {/* Right half — triangular slice of the play triangle */}
        <path
          d="M12.25 6.1 L12.25 17.9 L21.5 12 Z"
          className="fill-text-primary"
        />
      </svg>
      {showWordmark && (
        <span className="text-lg font-semibold tracking-tight text-text-primary">
          AUVI
        </span>
      )}
    </div>
  );
}







