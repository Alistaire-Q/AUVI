/**
 * Axios API client and all API call functions for AUVI.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Submit a YouTube URL for processing.
 * @param {string} url - YouTube video URL
 * @param {object} settings - Processing settings
 * @returns {Promise<{job_id: string}>}
 */
export async function processUrl(url, settings = {}) {
  const response = await api.post('/process', { url, settings });
  return response.data;
}

/**
 * Upload a video file for processing.
 * @param {File} file - Video file to upload
 * @param {object} settings - Processing settings
 * @param {function} onProgress - Progress callback (0-100)
 * @returns {Promise<{job_id: string, message: string}>}
 */
export async function uploadFile(file, settings = {}, onProgress = null) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('settings_json', JSON.stringify(settings));

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 min timeout for large uploads
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Get job metadata.
 * @param {string} jobId
 * @returns {Promise<object>}
 */
export async function getJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Subscribe to job progress via Server-Sent Events.
 * @param {string} jobId
 * @param {function} onProgress - Callback for progress events
 * @param {function} onComplete - Callback when job completes
 * @param {function} onError - Callback on error
 * @returns {EventSource} - The EventSource instance (call .close() to unsubscribe)
 */
export function subscribeToProgress(jobId, { onProgress, onComplete, onError }) {
  const eventSource = new EventSource(`/api/jobs/${jobId}/progress`);

  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onProgress) onProgress(data);
    } catch (e) {
      console.error('Failed to parse progress event:', e);
    }
  });

  eventSource.addEventListener('completed', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onComplete) onComplete(data);
    } catch (e) {
      console.error('Failed to parse completed event:', e);
    }
    eventSource.close();
  });

  eventSource.addEventListener('failed', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onError) onError(data.error || 'Processing failed');
    } catch (e) {
      if (onError) onError('Processing failed');
    }
    eventSource.close();
  });

  eventSource.addEventListener('cancelled', () => {
    eventSource.close();
  });

  eventSource.onerror = (event) => {
    console.error('SSE connection error:', event);
    // Don't call onError for connection drops — SSE auto-reconnects
  };

  return eventSource;
}

/**
 * Get all clips for a job.
 * @param {string} jobId
 * @returns {Promise<Array>}
 */
export async function getClips(jobId) {
  const response = await api.get(`/jobs/${jobId}/clips`);
  return response.data;
}

/**
 * Get clip download URL.
 * @param {string} clipId
 * @returns {string}
 */
export function getDownloadUrl(clipId) {
  return `/api/clips/${clipId}/download`;
}

/**
 * Delete/cancel a job.
 * @param {string} jobId
 * @returns {Promise<object>}
 */
export async function deleteJob(jobId) {
  const response = await api.delete(`/jobs/${jobId}`);
  return response.data;
}

export default api;
