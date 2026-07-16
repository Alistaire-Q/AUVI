import React, { useState } from 'react';
import { Youtube, ArrowRight, AlertCircle } from 'lucide-react';

export default function YouTubeInput({ onSubmitUrl }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (url) => {
    const regex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/|embed\/)|youtu\.be\/)[\w\-]{11}/;
    return regex.test(url);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    if (!validateUrl(url)) {
      setError('Please enter a valid YouTube video or Shorts URL');
      return;
    }

    if (onSubmitUrl) {
      onSubmitUrl(url);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative flex items-center w-full">
        <div className="pointer-events-none absolute left-4 text-text-muted">
          <Youtube className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste a YouTube video or Shorts link…"
          className="input-field h-12 pl-12 pr-36 text-base shadow-none text-text-primary"
        />
        <div className="absolute right-1.5">
          <button
            type="submit"
            disabled={!url.trim()}
            className="btn-primary py-2 px-4 shadow-none gap-1.5"
          >
            <span>Options</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-danger text-sm animate-fade-in pl-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
