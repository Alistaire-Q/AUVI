import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CloudDownload, AudioWaveform, Brain, Scissors, Captions, CheckCircle, AlertCircle, Loader2, Sparkles } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Fetching source', icon: CloudDownload, detail: 'Connecting to the link and pulling the highest-quality stream.' },
  { id: 2, label: 'Transcribing', icon: AudioWaveform, detail: 'Whisper-grade ASR with word-level timestamps.' },
  { id: 3, label: 'Analyzing', icon: Brain, detail: 'Detecting hooks, payoffs, emotion spikes and pattern interrupts.' },
  { id: 4, label: 'Generating clips', icon: Scissors, detail: 'Rendering ready-to-post clips with titles and scores.' },
];

const STEP_ICONS = [CloudDownload, AudioWaveform, Brain, Scissors, Captions, Sparkles];

export default function ProcessingSteps({ currentStep, progress, message, status, error }) {
  // Lightweight animated waveform + score bars for the live preview panel
  const [waveform, setWaveform] = useState(() =>
    Array.from({ length: 48 }, () => 0.2 + Math.random() * 0.8),
  );
  const [scoreBars, setScoreBars] = useState(() => Array.from({ length: 5 }, () => 0));

  const active = status !== 'failed' && status !== 'completed' && currentStep > 0;

  useEffect(() => {
    if (!active) return;
    const interval = setInterval(() => {
      setWaveform((prev) =>
        prev.map((b, i) => {
          const target = 0.3 + 0.7 * Math.abs(Math.sin(Date.now() / 220 + i * 0.5));
          return b + (target - b) * 0.4;
        }),
      );
    }, 90);
    return () => clearInterval(interval);
  }, [active]);

  useEffect(() => {
    if (!active) return;
    const targets = [94, 88, 82, 76, 70];
    const interval = setInterval(() => {
      setScoreBars((prev) => prev.map((b, i) => Math.min(targets[i], b + 5)));
    }, 120);
    return () => clearInterval(interval);
  }, [active]);

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-balance text-2xl font-semibold tracking-tight md:text-3xl">
          {status === 'failed' ? 'Processing failed' : status === 'completed' ? 'All done!' : 'AUVI is working its magic'}
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
          {message || (status === 'failed' ? 'Something went wrong.' : 'Analyzing your video…')}
        </p>
      </div>

      {/* Overall progress */}
      <div className="mx-auto max-w-md">
        <div className="flex items-center justify-between text-xs text-text-muted mb-1.5">
          <span>Progress</span>
          <span className="font-mono font-semibold text-accent-1">{progress}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-surface">
          <motion.div
            className="h-full auvi-gradient-brand"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Steps + live preview */}
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {/* Step list */}
        <div className="space-y-2">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id && status !== 'failed';
            const isCompleted = currentStep > step.id || status === 'completed';
            const isFailed = currentStep === step.id && status === 'failed';
            const isPending = currentStep < step.id;

            return (
              <motion.div
                key={step.id}
                layout
                className={`relative flex items-start gap-3 rounded-xl border p-3.5 backdrop-blur transition-colors ${
                  isActive ? 'border-accent-1/40 bg-accent-1/5'
                  : isFailed ? 'border-danger/50 bg-danger/5'
                  : isPending ? 'border-border bg-card/30 opacity-60'
                  : 'border-border bg-card/40'
                }`}
              >
                <div
                  className={`grid size-8 shrink-0 place-items-center rounded-lg transition-colors ${
                    isCompleted ? 'bg-accent-1/15 text-accent-1'
                    : isActive ? 'auvi-gradient-brand text-white'
                    : isFailed ? 'bg-danger/15 text-danger'
                    : 'bg-surface text-text-muted'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : isFailed ? (
                    <AlertCircle className="w-4 h-4" />
                  ) : isActive ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-sm font-medium ${isPending ? 'text-text-muted' : 'text-text-primary'}`}>
                      {step.label}
                    </p>
                    <span className="text-[10px] font-mono text-text-muted">
                      {String(i + 1).padStart(2, '0')}/{String(STEPS.length).padStart(2, '0')}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-text-muted">{step.detail}</p>
                </div>
              </motion.div>
            );
          })}

          {/* Failure detail */}
          {status === 'failed' && (
            <div className="rounded-xl border border-danger/50 bg-danger/5 p-3.5 flex items-start gap-3">
              <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-danger/15 text-danger">
                <AlertCircle className="w-4 h-4" />
              </div>
              <p className="text-xs text-text-muted">{error || 'An unexpected error occurred during processing.'}</p>
            </div>
          )}
        </div>

        {/* Live preview panel */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-xl border border-border bg-card/60 p-4 backdrop-blur"
        >
          <div className="mb-3 flex items-center gap-2 text-xs font-medium text-text-muted">
            <Brain className="w-3.5 h-3.5 text-accent-1" />
            {status === 'completed' ? 'Composing your clips' : 'Live analysis'}
            {active && (
              <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-accent-1">
                <span className="size-1.5 animate-pulse rounded-full bg-accent-1" />
                streaming
              </span>
            )}
          </div>

          {status === 'completed' ? (
            <div className="py-6 text-center">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="mx-auto grid size-12 place-items-center rounded-full bg-accent-1/15 text-accent-1"
              >
                <CheckCircle className="w-6 h-6" />
              </motion.div>
              <p className="mt-3 text-sm font-medium">Clips ready to ship</p>
              <p className="mt-1 text-xs text-text-muted">Routing you to your dashboard…</p>
            </div>
          ) : status === 'failed' ? (
            <p className="py-6 text-center text-xs text-text-muted">Analysis interrupted.</p>
          ) : (
            <>
              {/* Waveform */}
              <div className="flex h-20 items-end justify-between gap-0.5">
                {waveform.map((b, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t-sm auvi-gradient-brand transition-all"
                    style={{ height: `${Math.max(6, b * 100)}%`, opacity: 0.5 + b * 0.5 }}
                  />
                ))}
              </div>
              {/* Score bars */}
              <div className="mt-4 space-y-2">
                {scoreBars.map((score, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="w-16 shrink-0 text-[11px] text-text-muted">Clip {i + 1}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                      <motion.div
                        className="h-full auvi-gradient-brand"
                        animate={{ width: `${score}%` }}
                        transition={{ duration: 0.2 }}
                      />
                    </div>
                    <span className="w-9 shrink-0 text-right text-[11px] font-mono font-medium text-accent-1">{score}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}
