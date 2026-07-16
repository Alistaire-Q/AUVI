import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileVideo, AlertCircle } from 'lucide-react';

const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
const ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.webm'];
const MAX_SIZE = 500 * 1024 * 1024; // 500MB

export default function UploadZone({ onFileSelect }) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');


  const validateFile = useCallback((file) => {
    if (!file) return 'No file selected';

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported format: ${ext}. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }

    if (file.size > MAX_SIZE) {
      return `File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum: 500MB`;
    }

    return null;
  }, []);

  const handleFile = useCallback(async (file) => {
    setError('');
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    if (onFileSelect) {
      onFileSelect(file);
    }
  }, [validateFile, onFileSelect]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileSelect = useCallback((e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  }, [handleFile]);

  return (
    <div className="w-full">
      <div
        className={`upload-zone relative flex flex-col items-center justify-center px-6 py-10 cursor-pointer transition-all ${
          dragOver ? 'drag-over' : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label="Upload video file"
        id="upload-zone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.mov,.avi,.webm"
          onChange={handleFileSelect}
          className="hidden"
          id="file-input"
        />

          <div className="flex flex-col items-center gap-3">
            <div className="grid w-12 h-12 place-items-center rounded-full bg-accent-1/15 text-accent-1">
              <Upload className="w-5 h-5" />
            </div>
            <div className="text-center">
              <p className="text-text-primary font-medium text-sm">
                Drop a video file or click to browse
              </p>
              <p className="mt-1 text-text-muted text-xs">
                Up to 500MB · MP4, MOV, AVI, WebM
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleClick();
              }}
              className="btn-primary py-2 px-4 text-sm shadow-none gap-1.5"
            >
              <Upload className="w-4 h-4" />
              Choose file
            </button>
          </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-3 flex items-center gap-2 text-danger text-sm animate-fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
