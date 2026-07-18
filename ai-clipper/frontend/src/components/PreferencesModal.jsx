import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Smartphone, Monitor, Square, AlignLeft, Tag, Loader2, Save } from 'lucide-react';

export default function PreferencesModal({ isOpen, onClose }) {
  const [frameSize, setFrameSize] = useState('9:16');
  const [subtitlePosition, setSubtitlePosition] = useState('bottom');
  const [defaultTags, setDefaultTags] = useState('#shorts #podcast');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      fetch('http://localhost:8000/api/youtube/preferences')
        .then(res => res.json())
        .then(data => {
          if (data && !data.detail) {
            if (data.frame_size) setFrameSize(data.frame_size);
            if (data.subtitle_position) setSubtitlePosition(data.subtitle_position);
            if (data.default_tags) setDefaultTags(data.default_tags);
          }
          setIsLoading(false);
        })
        .catch(err => {
          console.error(err);
          setIsLoading(false);
        });
    }
  }, [isOpen]);

  const handleSave = () => {
    setIsSaving(true);
    fetch('http://localhost:8000/api/youtube/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        frame_size: frameSize,
        subtitle_position: subtitlePosition,
        subtitle_style: 'tiktok',
        default_tags: defaultTags
      })
    })
      .then(res => res.json())
      .then(() => {
        setIsSaving(false);
        onClose();
      })
      .catch(err => {
        console.error(err);
        setIsSaving(false);
      });
  };

  if (!isOpen) return null;

  const frameOptions = [
    { id: '9:16', icon: Smartphone, label: 'Vertical', desc: 'TikTok, Reels, Shorts' },
    { id: '16:9', icon: Monitor, label: 'Horizontal', desc: 'YouTube, Web' },
    { id: '1:1', icon: Square, label: 'Square', desc: 'Instagram, LinkedIn' },
  ];

  const positionOptions = [
    { id: 'top', label: 'Top' },
    { id: 'middle', label: 'Middle' },
    { id: 'bottom', label: 'Bottom' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={isSaving ? undefined : onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative z-10 w-full max-w-3xl min-h-[500px] max-h-[90vh] flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xl overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-slate-100 p-6 shrink-0 bg-white">
              <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
                <Settings className="w-6 h-6 text-emerald-600" />
                Permanent Webhook Style
              </h2>
              <button
                onClick={onClose}
                disabled={isSaving}
                className="rounded-lg p-2 hover:bg-slate-100 text-slate-400 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 p-8 space-y-8 overflow-y-auto bg-white">
              {isLoading ? (
                <div className="flex justify-center items-center py-20">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    <label className="text-base font-medium text-slate-900">Frame Size (Aspect Ratio)</label>
                    <div className="grid grid-cols-3 gap-4">
                      {frameOptions.map((opt) => {
                        const Icon = opt.icon;
                        const active = frameSize === opt.id;
                        return (
                          <button
                            key={opt.id}
                            onClick={() => setFrameSize(opt.id)}
                            disabled={isSaving}
                            className={`flex flex-col items-center justify-center p-5 rounded-xl border text-center transition-all ${
                              active
                                ? 'border-emerald-600 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600'
                                : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-slate-300 hover:bg-slate-100'
                            }`}
                          >
                            <Icon className="w-8 h-8 mb-3" />
                            <span className={`text-base font-semibold ${active ? 'text-emerald-700' : 'text-slate-900'}`}>{opt.label}</span>
                            <span className="text-sm opacity-80 mt-1">{opt.desc}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <label className="text-base font-medium text-slate-900 flex items-center gap-2">
                      <AlignLeft className="w-5 h-5" />
                      Subtitle Position
                    </label>
                    <div className="flex bg-slate-50 rounded-xl p-1.5 border border-slate-200">
                      {positionOptions.map((opt) => (
                        <button
                          key={opt.id}
                          onClick={() => setSubtitlePosition(opt.id)}
                          disabled={isSaving}
                          className={`flex-1 py-3 text-sm font-medium rounded-lg transition-all ${
                            subtitlePosition === opt.id
                              ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                              : 'text-slate-500 hover:text-slate-900'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <label className="text-base font-medium text-slate-900 flex items-center gap-2">
                      <Tag className="w-5 h-5" />
                      Default YouTube Tags
                    </label>
                    <input
                      type="text"
                      value={defaultTags}
                      onChange={(e) => setDefaultTags(e.target.value)}
                      disabled={isSaving}
                      placeholder="#shorts #podcast #auvi"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-600/20 focus:border-emerald-600 transition-all"
                    />
                    <p className="text-sm text-slate-500">These tags will be automatically added to all clips uploaded via webhook.</p>
                  </div>
                </>
              )}
            </div>

            <div className="border-t border-slate-100 bg-slate-50 p-6 flex justify-end gap-4 shrink-0">
              <button
                onClick={onClose}
                disabled={isSaving}
                className="py-2.5 px-6 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || isLoading}
                className="py-2.5 px-8 rounded-xl bg-slate-900 text-white text-sm font-semibold shadow-sm hover:shadow-md hover:bg-slate-800 flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save Preferences
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function Settings({ className }) {
  return (
    <svg xmlns="http://www.w3.org/2005/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}
