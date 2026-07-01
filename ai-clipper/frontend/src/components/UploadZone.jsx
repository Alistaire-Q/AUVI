/**
 * UploadZone — Drag & drop file upload area with animated gradient border,
 * file validation, and upload progress bar.
 */

import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileVideo, AlertCircle } from 'lucide-react';
import useClipStore from '../store/useClipStore';
import { uploadFile } from '../lib/api';
import { useNavigate } from 'react-router-dom';

const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
const ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.webm'];
const MAX_SIZE = 500 * 1024 * 1024; // 500MB

export default function UploadZone() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);

  const { settings, setUploadProgress, addRecentProject } = useClipStore();

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

    setSelectedFile(file);
    setUploading(true);
    setUploadPercent(0);

    try {
      const result = await uploadFile(file, settings, (percent) => {
        setUploadPercent(percent);
        setUploadProgress(percent);
      });

      // Save to recent projects
      addRecentProject({
        id: result.job_id,
        title: file.name,
        source: 'upload',
        date: new Date().toISOString(),
      });

      // Navigate to processing page
      navigate(`/processing/${result.job_id}`);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Upload failed';
      setError(message);
      setUploading(false);
      setUploadPercent(0);
    }
  }, [settings, navigate, validateFile, setUploadProgress, addRecentProject]);

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
    if (!uploading) {
      fileInputRef.current?.click();
    }
  }, [uploading]);

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
        } ${uploading ? 'pointer-events-none opacity-70' : ''}`}
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

        {uploading ? (
          <div className="flex flex-col items-center gap-4 animate-fade-in">
            <div className="w-14 h-14 rounded-2xl auvi-gradient-brand auvi-glow-soft flex items-center justify-center">
              <FileVideo className="w-7 h-7 text-white animate-pulse" />
            </div>
            <div className="text-center">
              <p className="text-text-primary font-semibold text-base mb-1">
                Uploading {selectedFile?.name}
              </p>
              <p className="text-text-muted text-sm">
                {(selectedFile?.size / 1024 / 1024).toFixed(1)}MB • {uploadPercent}%
              </p>
            </div>
            <div className="w-full max-w-xs">
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${uploadPercent}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
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
        )}
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
