import React, { useState } from 'react';
import { Youtube, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { processUrl } from '../lib/api';
import useClipStore from '../store/useClipStore';

export default function YouTubeInput() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { settings, addRecentProject } = useClipStore();

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

    setIsLoading(true);

    try {
      const result = await processUrl(url, settings);
      
      addRecentProject({
        id: result.job_id,
        title: url,
        source: 'youtube',
        date: new Date().toISOString(),
      });

      navigate(`/processing/${result.job_id}`);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to process URL';
      setError(message);
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative flex items-center w-full">
        <div className="absolute left-4 text-text-muted">
          <Youtube className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste YouTube URL here..."
          className="input-field pl-12 pr-32 py-4 text-base shadow-lg text-white"
          disabled={isLoading}
        />
        <div className="absolute right-2">
          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="btn-primary py-2 px-4 shadow-none"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <span>Process</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
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
