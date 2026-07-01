import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings, Link2, Upload, Sparkles, PlaySquare, Video, Gauge, Captions, Crop, Wand2, TrendingUp, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import YouTubeInput from '../components/YouTubeInput';
import SettingsDrawer from '../components/SettingsDrawer';
import Logo from '../components/Logo';
import useClipStore from '../store/useClipStore';

const FEATURES = [
  { icon: Gauge, title: 'Virality scoring', description: 'Every clip gets a 0–100 score so you know which moments will pop.' },
  { icon: Captions, title: 'Animated captions', description: 'Word-by-word captions auto-styled for maximum retention.' },
  { icon: Crop, title: 'Auto 9:16 reframing', description: 'Active-speaker tracking keeps the talent centered for vertical.' },
  { icon: Wand2, title: 'AI hook extraction', description: 'AUVI finds the strongest moments so you never edit from scratch.' },
];

const STATS = [
  { value: '100%', label: 'Local & private' },
  { value: '4-step', label: 'AI pipeline' },
  { value: 'Whisper', label: 'Grade transcription' },
  { value: 'MP4', label: 'Ready-to-post clips' },
];

export default function Home() {
  const { toggleSettings, getRecentProjects } = useClipStore();
  const recentProjects = getRecentProjects();
  const [mode, setMode] = useState('link');

  return (
    <div className="min-h-screen bg-base relative overflow-hidden flex flex-col">
      {/* Ambient backdrop */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-accent-1/20 blur-[140px]" />
        <div className="absolute top-40 -right-32 h-[320px] w-[420px] rounded-full bg-accent-2/15 blur-[120px]" />
        <div className="absolute top-20 -left-32 h-[280px] w-[380px] rounded-full bg-orange-500/10 blur-[120px]" />
        <div className="absolute inset-0 auvi-grid-bg opacity-30 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
      </div>

      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-4 md:px-6 py-5 flex justify-between items-center">
        <Logo size={36} />
        <button
          onClick={toggleSettings}
          className="p-2 rounded-lg hover:bg-surface border border-transparent hover:border-border text-text-muted hover:text-text-primary transition-all flex items-center gap-2"
        >
          <Settings className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline-block">Settings</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-grow flex flex-col items-center w-full max-w-6xl mx-auto px-4 md:px-6 pt-6 pb-16 md:pt-10">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs text-text-muted backdrop-blur">
            <span className="size-1.5 rounded-full bg-accent-1 auvi-pulse-ring" />
            100% Free & Local Processing
          </div>

          <h1 className="mx-auto max-w-3xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl md:text-6xl leading-tight">
            Turn long videos into
            <br className="hidden sm:block" />{' '}
            <span className="auvi-gradient-text">viral short clips</span> with one click.
          </h1>

          <p className="mx-auto mt-5 max-w-xl text-pretty text-sm text-text-muted md:text-base">
            Upload a video or paste a YouTube link. AUVI analyzes the content,
            finds the most engaging moments, and ships vertical clips with captions — ready to post.
          </p>
        </motion.div>

        {/* Uploader card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mx-auto mt-8 w-full max-w-3xl"
        >
          <div className="auvi-glow rounded-2xl border border-border bg-card/80 p-5 backdrop-blur-xl md:p-6">
            {/* Mode switch */}
            <div className="mb-5 inline-flex rounded-xl border border-border bg-surface/60 p-1">
              <button
                onClick={() => setMode('link')}
                className={`flex items-center gap-2 rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                  mode === 'link'
                    ? 'auvi-gradient-brand text-white shadow-sm'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                <Link2 className="w-4 h-4" />
                Paste link
              </button>
              <button
                onClick={() => setMode('upload')}
                className={`flex items-center gap-2 rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                  mode === 'upload'
                    ? 'auvi-gradient-brand text-white shadow-sm'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                <Upload className="w-4 h-4" />
                Upload file
              </button>
            </div>

            {mode === 'link' ? (
              <div className="space-y-3">
                <YouTubeInput />
                <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
                  {['YouTube', 'Shorts', 'youtu.be'].map((f) => (
                    <span key={f} className="rounded-md bg-surface px-2 py-1">{f}</span>
                  ))}
                </div>
              </div>
            ) : (
              <UploadZone />
            )}
          </div>

          {/* Trending-style chips (format support) */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-xs">
            <span className="flex items-center gap-1.5 text-text-muted">
              <TrendingUp className="w-3.5 h-3.5" />
              Supports:
            </span>
            {['MP4', 'MOV', 'AVI', 'WebM', 'YouTube URL'].map((format) => (
              <span key={format} className="rounded-full border border-border bg-card/60 px-3 py-1 text-text-muted">
                {format}
              </span>
            ))}
          </div>
        </motion.div>

        {/* Recent Projects (if any) */}
        {recentProjects.length > 0 && (
          <section className="mt-14 w-full">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <h2 className="text-lg font-semibold tracking-tight md:text-xl flex items-center gap-2">
                  <PlaySquare className="w-5 h-5 text-accent-1" />
                  Recent projects
                </h2>
                <p className="mt-1 text-sm text-text-muted">Jump back into a video you processed.</p>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {recentProjects.map((project, i) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                >
                  <Link
                    to={`/dashboard/${project.id}`}
                    className="group block h-full p-4 text-left transition-all hover:border-accent-1/40"
                  >
                    <div className="card flex items-start gap-3">
                      <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent-1/15 text-accent-1">
                        {project.source === 'youtube' ? <Video className="w-4 h-4" /> : <PlaySquare className="w-4 h-4" />}
                      </div>
                      <div className="min-w-0 flex-1 overflow-hidden">
                        <p className="text-sm font-medium text-text-primary truncate" title={project.title}>
                          {project.title}
                        </p>
                        <p className="mt-1 text-xs text-text-muted">
                          {new Date(project.date).toLocaleDateString()}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-text-muted opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </section>
        )}

        {/* Feature strip */}
        <section className="mt-16 w-full">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2 + i * 0.05 }}
                className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur"
              >
                <div className="grid size-10 place-items-center rounded-xl bg-accent-1/15 text-accent-1">
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="mt-3 text-sm font-semibold">{f.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-text-muted">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Stats band */}
        <section className="mt-8 w-full">
          <div className="grid gap-4 rounded-2xl border border-border bg-card/60 p-6 backdrop-blur md:grid-cols-4 md:p-8">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center md:text-left">
                <div className="text-2xl font-semibold tracking-tight md:text-3xl">
                  <span className="auvi-gradient-text">{stat.value}</span>
                </div>
                <p className="mt-1 text-xs text-text-muted">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mt-16 text-center">
          <h2 className="text-balance text-2xl font-semibold tracking-tight md:text-3xl">
            Your next viral clip is hiding
            <br className="hidden sm:block" /> in a video you already have.
          </h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-text-muted">
            Drop a link above and AUVI will surface it in minutes — captions included.
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-text-muted">
              <CheckCircle2 className="w-3.5 h-3.5 text-accent-1" />
              No credit card required
            </div>
          </div>
        </section>

        <footer className="mt-20 w-full border-t border-border pt-6 text-center text-xs text-text-muted">
          <p className="flex items-center justify-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-accent-1" />
            © {new Date().getFullYear()} AUVI · Built for creators who ship daily.
          </p>
        </footer>
      </main>

      <SettingsDrawer />
    </div>
  );
}
