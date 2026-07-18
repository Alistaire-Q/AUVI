/**
 * Zustand store for AUVI global state.
 * Manages job data, clips, settings, filters, and UI state.
 */

import { create } from 'zustand';

const DEFAULT_SETTINGS = {
  clip_duration: 30,
  max_clips: 5,
  language: 'auto',
  caption_style: 'word',
  min_score: 20,
  subtitle_enabled: true,
  subtitle_position: 'bottom',
  subtitle_font_size: 'medium',
  subtitle_style: 'tiktok',
  frame_size: '9:16',
};

const useClipStore = create((set, get) => ({
  // ─── Job State ───
  currentJob: null,
  setCurrentJob: (job) => set({ currentJob: job }),

  // ─── Clips ───
  clips: [],
  setClips: (clips) => set({ clips }),

  // ─── Selected Clip (for preview modal) ───
  selectedClip: null,
  setSelectedClip: (clip) => set({ selectedClip: clip }),
  clearSelectedClip: () => set({ selectedClip: null }),

  // ─── Processing State ───
  processing: {
    step: 0,
    progress: 0,
    message: '',
    status: 'idle',
    error: null,
  },
  setProcessing: (update) =>
    set((state) => ({
      processing: { ...state.processing, ...update },
    })),
  resetProcessing: () =>
    set({
      processing: {
        step: 0,
        progress: 0,
        message: '',
        status: 'idle',
        error: null,
      },
    }),

  // ─── Settings ───
  settings: { ...DEFAULT_SETTINGS },
  updateSettings: (update) =>
    set((state) => ({
      settings: { ...state.settings, ...update },
    })),
  resetSettings: () => set({ settings: { ...DEFAULT_SETTINGS } }),

  // ─── Filters ───
  filter: 'all', // 'all' | 'high' | 'medium' | 'short'
  setFilter: (filter) => set({ filter }),

  sortBy: 'score', // 'score' | 'duration' | 'position'
  setSortBy: (sortBy) => set({ sortBy }),

  // ─── UI State ───
  settingsOpen: false,
  language: 'en', // 'en' or 'id'
  setLanguage: (lang) => set({ language: lang }),
  toggleSettings: () => set((state) => ({ settingsOpen: !state.settingsOpen })),
  closeSettings: () => set({ settingsOpen: false }),

  previewOpen: false,
  openPreview: (clip) => set({ previewOpen: true, selectedClip: clip }),
  closePreview: () => set({ previewOpen: false, selectedClip: null }),

  // ─── Upload State ───
  uploadProgress: 0,
  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  // ─── Filtered & Sorted Clips ───
  getFilteredClips: () => {
    const { clips, filter, sortBy } = get();

    let filtered = [...clips];

    // Apply filter
    switch (filter) {
      case 'high':
        filtered = filtered.filter((c) => c.score >= 70);
        break;
      case 'medium':
        filtered = filtered.filter((c) => c.score >= 40 && c.score < 70);
        break;
      case 'short':
        filtered = filtered.filter((c) => c.duration < 30);
        break;
      default:
        break;
    }

    // Apply sort
    switch (sortBy) {
      case 'score':
        filtered.sort((a, b) => b.score - a.score);
        break;
      case 'duration':
        filtered.sort((a, b) => b.duration - a.duration);
        break;
      case 'position':
        filtered.sort((a, b) => a.start - b.start);
        break;
      default:
        break;
    }

    return filtered;
  },

  // ─── Recent Projects (localStorage) ───
  getRecentProjects: () => {
    try {
      const stored = localStorage.getItem('ai-clipper-recent');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },

  addRecentProject: (project) => {
    try {
      const recent = get().getRecentProjects();
      const updated = [
        project,
        ...recent.filter((p) => p.id !== project.id),
      ].slice(0, 10);
      localStorage.setItem('ai-clipper-recent', JSON.stringify(updated));
    } catch {
      // localStorage might be unavailable
    }
  },
}));

export default useClipStore;
