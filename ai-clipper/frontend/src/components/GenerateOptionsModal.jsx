import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Crop, AlignLeft, Smartphone, Monitor, Square, Loader2, Type } from 'lucide-react';
import useClipStore from '../store/useClipStore';

export default function GenerateOptionsModal({ isOpen, onClose, onGenerate, isLoading, pendingType, uploadProgress }) {
  const { settings, updateSettings, language } = useClipStore();
  
  // Local state so we don't apply immediately until they click Generate
  const [frameSize, setFrameSize] = useState(settings.frame_size || '9:16');
  const [subtitlePosition, setSubtitlePosition] = useState(settings.subtitle_position || 'bottom');
  const [subtitleStyle, setSubtitleStyle] = useState(settings.subtitle_style || 'bold_viral');

  if (!isOpen) return null;

  const handleGenerate = () => {
    updateSettings({
      frame_size: frameSize,
      subtitle_position: subtitlePosition,
      subtitle_style: subtitleStyle,
    });
    onGenerate();
  };

  const frameOptions = [
    { id: '9:16', icon: Smartphone, label: 'Vertical', desc: 'TikTok, Reels, Shorts' },
    { id: '16:9', icon: Monitor, label: 'Horizontal', desc: 'YouTube, Web' },
    { id: '1:1', icon: Square, label: 'Square', desc: 'Instagram, LinkedIn' },
  ];

  const positionOptions = [
    { id: 'top', label: 'Top (Atas)' },
    { id: 'middle', label: 'Middle (Tengah)' },
    { id: 'bottom', label: 'Bottom (Bawah)' },
  ];

  const subtitleTemplates = [
    { 
      id: 'cinematic', 
      label: 'Cinematic', 
      desc: language === 'id' ? 'Elegan & minimalis' : 'Elegant & minimal',
      font: '#FFFFFF', 
      highlight: '#FFE6C8',
      bg: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    },
    { 
      id: 'bold_viral', 
      label: 'Bold Viral', 
      desc: language === 'id' ? 'Energik ala TikTok' : 'TikTok-style energy',
      font: '#FFFFFF', 
      highlight: '#FFD700',
      bg: 'linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%)',
    },
    { 
      id: 'soft_edu', 
      label: 'Soft Edu', 
      desc: language === 'id' ? 'Tenang & edukatif' : 'Calm & educational',
      font: '#FFF0F0', 
      highlight: '#A0D4FF',
      bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    },
    { 
      id: 'corporate', 
      label: 'Corporate', 
      desc: language === 'id' ? 'Profesional' : 'Professional',
      font: '#FFFFFF', 
      highlight: '#80D080',
      bg: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
    },
    { 
      id: 'dark_mode', 
      label: 'Dark Mode', 
      desc: language === 'id' ? 'Modern & gelap' : 'Modern & dark',
      font: '#E0E0E0', 
      highlight: '#00FFFF',
      bg: 'linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%)',
    },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-base/80 backdrop-blur-sm"
            onClick={isLoading ? undefined : onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative z-10 w-full max-w-3xl min-h-[500px] max-h-[90vh] flex flex-col rounded-2xl border border-border bg-card shadow-xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border p-6 shrink-0 bg-card">
              <h2 className="text-xl font-semibold text-text-primary flex items-center gap-2">
                <Crop className="w-6 h-6 text-accent-1" />
                {language === 'id' ? 'Pengaturan Klip' : 'Clip Settings'}
              </h2>
              <button
                onClick={onClose}
                disabled={isLoading}
                className="rounded-lg p-2 hover:bg-card-hover text-text-muted transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 p-8 space-y-8 overflow-y-auto bg-card">
              {/* Frame Size */}
              <div className="space-y-4">
                <label className="text-base font-medium text-text-primary">{language === 'id' ? 'Ukuran Bingkai (Rasio Aspek)' : 'Frame Size (Aspect Ratio)'}</label>
                <div className="grid grid-cols-3 gap-4">
                  {frameOptions.map((opt) => {
                    const Icon = opt.icon;
                    const active = frameSize === opt.id;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => setFrameSize(opt.id)}
                        disabled={isLoading}
                        className={`flex flex-col items-center justify-center p-5 rounded-xl border text-center transition-all ${
                          active
                            ? 'border-accent-1 bg-accent-1/10 text-accent-1 ring-1 ring-accent-1'
                            : 'border-border bg-surface text-text-muted hover:border-text-primary hover:bg-card-hover'
                        }`}
                      >
                        <Icon className="w-8 h-8 mb-3" />
                        <span className={`text-base font-semibold text-text-primary`}>{opt.id}</span>
                        <span className="text-sm opacity-80 mt-1">{opt.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Subtitle Style Template */}
              <div className="space-y-4">
                <label className="text-base font-medium text-text-primary flex items-center gap-2">
                  <Type className="w-5 h-5" />
                  {language === 'id' ? 'Gaya Subtitle' : 'Subtitle Style'}
                </label>
                <div className="grid grid-cols-5 gap-3">
                  {subtitleTemplates.map((tmpl) => {
                    const active = subtitleStyle === tmpl.id;
                    return (
                      <button
                        key={tmpl.id}
                        onClick={() => setSubtitleStyle(tmpl.id)}
                        disabled={isLoading}
                        className={`flex flex-col items-center p-3 rounded-xl border text-center transition-all ${
                          active
                            ? 'border-accent-1 ring-2 ring-accent-1 shadow-lg scale-[1.02]'
                            : 'border-border hover:border-text-muted hover:shadow-md'
                        }`}
                      >
                        {/* Mini Preview Box */}
                        <div
                          className="w-full h-14 rounded-lg mb-2 flex items-center justify-center overflow-hidden"
                          style={{ background: tmpl.bg }}
                        >
                          <span className="text-xs font-bold tracking-wide" style={{ color: tmpl.font }}>
                            HELLO{' '}
                            <span style={{ color: tmpl.highlight, fontSize: '14px' }}>WORLD</span>
                          </span>
                        </div>
                        <span className="text-xs font-semibold text-text-primary leading-tight">{tmpl.label}</span>
                        <span className="text-[10px] text-text-muted mt-0.5 leading-tight">{tmpl.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Subtitle Position */}
              <div className="space-y-4">
                <label className="text-base font-medium text-text-primary flex items-center gap-2">
                  <AlignLeft className="w-5 h-5" />
                  {language === 'id' ? 'Posisi Takarir' : 'Subtitle Position'}
                </label>
                <div className="flex bg-surface rounded-xl p-1.5 border border-border">
                  {positionOptions.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setSubtitlePosition(opt.id)}
                      disabled={isLoading}
                      className={`flex-1 py-3 text-sm font-medium rounded-lg transition-all ${
                        subtitlePosition === opt.id
                          ? 'bg-card text-text-primary shadow-sm border border-border'
                          : 'text-text-muted hover:text-text-primary'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Progress / Status (if file upload) */}
              {isLoading && pendingType === 'upload' && (
                 <div className="space-y-3 mt-4 bg-surface p-4 rounded-xl border border-border">
                   <div className="flex justify-between text-sm text-text-muted mb-2">
                     <span className="text-text-primary">{language === 'id' ? 'Mengunggah file...' : 'Uploading file...'}</span>
                     <span className="text-text-primary font-medium">{uploadProgress}%</span>
                   </div>
                   <div className="progress-bar bg-border h-2 rounded-full overflow-hidden">
                     <div className="progress-bar-fill h-full bg-accent-1 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                   </div>
                 </div>
              )}
              
              {isLoading && pendingType === 'link' && (
                <div className="flex items-center justify-center gap-3 text-base text-text-primary mt-4 bg-surface p-5 rounded-xl border border-border">
                  <Loader2 className="w-5 h-5 animate-spin text-accent-1" />
                  <span>{language === 'id' ? 'Memproses URL YouTube...' : 'Processing YouTube URL...'}</span>
                </div>
              )}

            </div>

            {/* Footer */}
            <div className="border-t border-border bg-surface p-6 flex justify-end gap-4 shrink-0">
              <button
                onClick={onClose}
                disabled={isLoading}
                className="py-2.5 px-6 rounded-xl text-sm font-medium text-text-primary hover:bg-card-hover transition-colors disabled:opacity-50"
              >
                {language === 'id' ? 'Batal' : 'Cancel'}
              </button>
              <button
                onClick={handleGenerate}
                disabled={isLoading}
                className="py-2.5 px-8 rounded-xl bg-text-primary text-base text-sm font-semibold shadow-sm hover:opacity-90 flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                {language === 'id' ? 'Buat Klip' : 'Generate Clip'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
