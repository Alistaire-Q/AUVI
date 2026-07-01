import React from 'react';

/**
 * AuviLogo — gradient brand tile with a stylized "A" + waveform glyph,
 * ported from the AUVI Z.ai prototype. Purely presentational.
 */
export default function Logo({ size = 32, showWordmark = true, className = '' }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <div
        className="relative grid place-items-center rounded-xl auvi-gradient-brand auvi-glow-soft"
        style={{ width: size, height: size }}
        aria-hidden
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="text-white"
          style={{ width: size * 0.62, height: size * 0.62 }}
        >
          {/* Stylized "A" formed by a play wedge + waveform */}
          <path
            d="M16 4L4 26h6l3-6h6l3 6h6L16 4z"
            fill="currentColor"
            fillOpacity="0.18"
          />
          <path
            d="M16 8l-7 16h3.4l1.1-2.6h5l1.1 2.6H23L16 8z"
            fill="currentColor"
          />
          <rect x="13.4" y="17.5" width="1.4" height="3.2" rx="0.7" fill="currentColor" opacity="0.55" />
          <rect x="15.3" y="16.4" width="1.4" height="5.4" rx="0.7" fill="currentColor" opacity="0.55" />
          <rect x="17.2" y="17.5" width="1.4" height="3.2" rx="0.7" fill="currentColor" opacity="0.55" />
        </svg>
      </div>
      {showWordmark && (
        <span className="text-lg font-semibold tracking-tight text-text-primary">
          AUVI
        </span>
      )}
    </div>
  );
}
