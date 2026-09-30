import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Crop, AlignLeft, Smartphone, Monitor, Square, Loader2, Type, Clapperboard, Flame, GraduationCap, Briefcase, Moon, Sparkles, CheckCircle2, TrendingUp, Users, Music, Diamond, Search } from 'lucide-react';
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
    { id: 'top', label: 'Top' },
    { id: 'middle', label: 'Middle' },
    { id: 'bottom', label: 'Bottom' },
  ];

  const subtitleTemplates = [
    {
      id: 'manifesto',
      label: 'Manifesto',
      desc: language === 'id' ? 'Bold serif statement' : 'Bold serif statement',
      previewIcon: Clapperboard,
      titleIcon: Sparkles,
      bg: 'linear-gradient(135deg, #1A0000 0%, #8B0000 50%, #CC0000 100%)',
      fontColor: '#FF0000',
      subColor: 'rgba(255,255,255,0.7)',
      fontFamily: 'Georgia, "Times New Roman", serif'
    },
    { 
      id: 'pro_accent', 
      label: 'Pro Accent', 
      desc: language === 'id' ? 'Aksen kuning profesional' : 'Professional yellow highlight',
      previewIcon: Flame,
      titleIcon: Flame,
      bg: 'linear-gradient(135deg, #1A1A2E 0%, #FFD700 100%)',
      fontColor: '#FFD700',
      subColor: 'rgba(255,255,255,0.8)',
      fontFamily: '"Montserrat", sans-serif'
    },
    {
      id: 'soft_edu',
      label: 'Soft Edu',
      desc: language === 'id' ? 'Tenang & edukatif' : 'Calm & educational',
      previewIcon: GraduationCap,
      titleIcon: GraduationCap,
      bg: 'linear-gradient(135deg, #E0E7FF 0%, #A78BFA 100%)',
      fontColor: '#4C1D95',
      subColor: 'rgba(76,29,149,0.7)',
      fontFamily: '"Roboto", sans-serif'
    },
    {
      id: 'corporate',
      label: 'Corporate',
      desc: language === 'id' ? 'Profesional' : 'Professional',
      previewIcon: Briefcase,
      titleIcon: Briefcase,
      bg: 'linear-gradient(135deg, #064E3B 0%, #0F766E 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(255,255,255,0.7)',
      fontFamily: '"Montserrat", sans-serif'
    },
    {
      id: 'dark_mode',
      label: 'Dark Mode',
      desc: language === 'id' ? 'Modern & gelap' : 'Modern & dark',
      previewIcon: Moon,
      titleIcon: Moon,
      bg: 'linear-gradient(135deg, #171717 0%, #3F3F46 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(255,255,255,0.6)',
      fontFamily: '"Roboto", sans-serif'
    },
    {
      id: 'market',
      label: 'Market',
      desc: language === 'id' ? 'Finansial & Bisnis' : 'Finance & Business',
      previewIcon: TrendingUp,
      titleIcon: TrendingUp,
      bg: 'linear-gradient(135deg, #00D964 0%, #FF3B30 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(255,255,255,0.8)',
      fontFamily: '"Oswald", sans-serif'
    },
    {
      id: 'duo',
      label: 'Duo',
      desc: language === 'id' ? 'Podcast 2 Pembicara' : 'Dual Speaker Podcast',
      previewIcon: Users,
      titleIcon: Users,
      bg: 'linear-gradient(135deg, #FFA630 0%, #2EC4B6 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(255,255,255,0.9)',
      fontFamily: '"Inter", sans-serif'
    },
    {
      id: 'pop',
      label: 'Pop',
      desc: language === 'id' ? 'Gen-Z & Hiburan' : 'Gen-Z & Entertainment',
      previewIcon: Music,
      titleIcon: Music,
      bg: 'linear-gradient(135deg, #FF3EA5 0%, #7B2FF7 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(255,255,255,0.9)',
      fontFamily: '"Baloo 2", sans-serif'
    },
    {
      id: 'noir',
      label: 'Noir',
      desc: language === 'id' ? 'Mewah & Premium' : 'Luxury & Premium',
      previewIcon: Diamond,
      titleIcon: Diamond,
      bg: 'linear-gradient(135deg, #D4AF37 0%, #1A1A1A 100%)',
      fontColor: '#FFFFFF',
      subColor: 'rgba(212,175,55,0.7)',
      fontFamily: '"Playfair Display", serif'
    },
    {
      id: 'casefile',
      label: 'Casefile',
      desc: language === 'id' ? 'Misteri & Dokumenter' : 'Mystery & Documentary',
      previewIcon: Search,
      titleIcon: Search,
      bg: 'linear-gradient(135deg, #8B0000 0%, #F5F1E8 100%)',
      fontColor: '#F5F1E8',
      subColor: 'rgba(245,241,232,0.7)',
      fontFamily: '"Bebas Neue", sans-serif'
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
                        className={`flex flex-col items-center justify-center p-5 rounded-xl border text-center transition-all ${active
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
                    const PreviewIcon = tmpl.previewIcon;
                    const TitleIcon = tmpl.titleIcon;
                    return (
                      <button
                        key={tmpl.id}
                        onClick={() => setSubtitleStyle(tmpl.id)}
                        disabled={isLoading}
                        className={`flex flex-col p-2 rounded-xl border bg-card transition-all ${active
                            ? 'border-accent-1 ring-1 ring-accent-1 shadow-sm scale-[1.02]'
                            : 'border-border hover:border-text-muted hover:shadow-sm'
                          }`}
                      >
                        {/* Mini Preview Box */}
                        <div
                          className="relative w-full h-24 rounded-lg p-3 flex flex-col justify-between overflow-hidden"
                          style={{ background: tmpl.bg }}
                        >
                          <div className="flex justify-between items-start w-full">
                            <PreviewIcon className="w-4 h-4" style={{ color: tmpl.subColor }} />
                            {active && (
                              <div className="bg-white rounded-full flex items-center justify-center w-5 h-5 shadow-sm">
                                <CheckCircle2 className="w-5 h-5 text-accent-1" />
                              </div>
                            )}
                          </div>

                          <div className="text-left mt-2" style={{ fontFamily: tmpl.fontFamily }}>
                            <div className="text-[10px] uppercase font-medium tracking-wide" style={{ color: tmpl.subColor }}>HELLO</div>
                            <div className="text-lg font-bold uppercase leading-none tracking-tight" style={{ color: tmpl.fontColor }}>WORLD</div>
                          </div>
                        </div>

                        <div className="mt-3 text-center w-full pb-1">
                          <div className="flex items-center justify-center gap-1.5">
                            <TitleIcon className="w-3.5 h-3.5 text-text-muted" />
                            <span className="text-xs font-semibold text-text-primary">{tmpl.label}</span>
                          </div>
                          <div className="text-[10px] text-text-muted mt-1 leading-tight">{tmpl.desc}</div>
                        </div>
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
                <div className="grid grid-cols-3 gap-4">
                  {positionOptions.map((opt) => {
                    const active = subtitlePosition === opt.id;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => setSubtitlePosition(opt.id)}
                        disabled={isLoading}
                        className={`flex items-center justify-center py-3 px-4 rounded-xl border text-center transition-all ${active
                            ? 'border-accent-1 bg-accent-1/10 text-accent-1 ring-1 ring-accent-1 font-semibold'
                            : 'border-border bg-surface text-text-muted hover:border-text-primary hover:bg-card-hover font-medium'
                          }`}
                      >
                        {opt.label}
                      </button>
                    );
                  })}
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
