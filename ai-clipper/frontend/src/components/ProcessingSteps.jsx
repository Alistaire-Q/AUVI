import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CloudDownload, AudioWaveform, Brain, Scissors, Captions, CheckCircle, AlertCircle, Loader2, Sparkles, AudioLines, Video } from 'lucide-react';

export default function ProcessingSteps({ currentStep, progress, message, status, error, language }) {
  const translateMessage = (msg) => {
    if (!msg || language !== 'id') return msg;
    if (msg === 'Downloading video from YouTube...') return 'Mengunduh video dari YouTube...';
    if (msg === 'File uploaded successfully') return 'File berhasil diunggah';
    if (msg.startsWith('Downloading...')) return msg.replace('Downloading...', 'Mengunduh...');
    if (msg === 'Extracting audio...') return 'Mengekstrak audio...';
    if (msg === 'Transcribing with Groq Whisper API...') return 'Mentranskripsi dengan Groq Whisper API...';
    if (msg === 'Transcription complete') return 'Transkripsi selesai';
    if (msg === 'Analyzing content for viral moments...') return 'Menganalisis konten untuk momen viral...';
    if (msg.startsWith('Found ') && msg.includes(' clip candidates')) return msg.replace('Found ', 'Ditemukan ').replace(' clip candidates', ' kandidat klip');
    if (msg === 'Generating clips...') return 'Membuat klip...';
    if (msg.startsWith('Generated clip ')) return msg.replace('Generated clip ', 'Memproses klip ');
    if (msg === 'All clips generated successfully!') return 'Semua klip berhasil dibuat!';
    return msg;
  };

  const STEPS = [
    { id: 1, label: language === 'id' ? 'Mengambil sumber' : 'Fetching source', icon: CloudDownload, detail: language === 'id' ? 'Menghubungkan ke tautan dan menarik kualitas stream terbaik.' : 'Connecting to the link and pulling the highest-quality stream.' },
    { id: 2, label: language === 'id' ? 'Mentranskripsi' : 'Transcribing', icon: AudioWaveform, detail: language === 'id' ? 'ASR level Whisper dengan stempel waktu per kata.' : 'Whisper-grade ASR with word-level timestamps.' },
    { id: 3, label: language === 'id' ? 'Menganalisis' : 'Analyzing', icon: Brain, detail: language === 'id' ? 'Mendeteksi hook, klimaks, emosi, dan interupsi pola.' : 'Detecting hooks, payoffs, emotion spikes and pattern interrupts.' },
    { id: 4, label: language === 'id' ? 'Membuat klip' : 'Generating clips', icon: Scissors, detail: language === 'id' ? 'Memproses klip siap tayang dengan judul dan skor.' : 'Rendering ready-to-post clips with titles and scores.' },
  ];
  // Lightweight animated waveform matrix for the Live Neural Hub
  const [waveform, setWaveform] = useState(() =>
    Array.from({ length: 36 }, () => 0.2 + Math.random() * 0.8),
  );

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

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-balance text-2xl font-semibold tracking-tight md:text-3xl">
          {status === 'failed' ? (language === 'id' ? 'Pemrosesan gagal' : 'Processing failed') : status === 'completed' ? (language === 'id' ? 'Semua selesai!' : 'All done!') : (language === 'id' ? 'AUVI sedang bekerja' : 'AUVI is working its magic')}
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
          {translateMessage(message) || (status === 'failed' ? (language === 'id' ? 'Terjadi kesalahan.' : 'Something went wrong.') : (language === 'id' ? 'Menganalisis video Anda...' : 'Analyzing your video…'))}
        </p>
      </div>

      {/* Overall progress */}
      <div className="mx-auto max-w-md">
        <div className="flex items-center justify-between text-xs text-text-muted mb-1.5">
          <span>{language === 'id' ? 'Progres' : 'Progress'}</span>
          <span className="font-mono font-semibold text-accent-1">{progress}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-border">
          <motion.div
            className="h-full bg-slate-900"
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
                    : isActive ? 'bg-slate-900 text-white'
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
              <p className="text-xs text-text-muted">{error || (language === 'id' ? 'Terjadi kesalahan tak terduga selama pemrosesan.' : 'An unexpected error occurred during processing.')}</p>
            </div>
          )}
        </div>

        {/* Live Neural Hub panel (Replaces fixed clip bars) */}
        <motion.div
          key="live-panel"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-2xl border border-accent-1/20 bg-gradient-to-br from-card/80 via-card/50 to-slate-900/60 p-5 backdrop-blur-xl shadow-lg shadow-black/20 flex flex-col justify-between"
        >
          <div>
            {/* Top Header */}
            <div className="mb-4 flex items-center justify-between pb-3 border-b border-border/50">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-text-primary">
                <div className="flex size-7 items-center justify-center rounded-lg bg-accent-1/15 text-accent-1 shadow-sm shadow-accent-1/20">
                  <Brain className="w-4 h-4 animate-pulse" />
                </div>
                <span>{language === 'id' ? 'Pusat Komputasi Neural AI' : 'AI Neural Computing Hub'}</span>
              </div>
              {active && (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-1/30 bg-accent-1/10 px-2.5 py-1 text-[10px] font-mono text-accent-1 tracking-wide uppercase">
                  <span className="size-1.5 animate-ping rounded-full bg-accent-1 mr-0.5" />
                  Live Tensor Engine
                </span>
              )}
            </div>

            {status === 'completed' ? (
              <div className="py-12 text-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="mx-auto grid size-14 place-items-center rounded-2xl bg-accent-1/20 text-accent-1 shadow-lg shadow-accent-1/30"
                >
                  <CheckCircle className="w-7 h-7" />
                </motion.div>
                <p className="mt-4 text-sm font-semibold text-text-primary">{language === 'id' ? 'Klip siap tayang!' : 'Clips ready to ship!'}</p>
                <p className="mt-1 text-xs text-text-muted">{language === 'id' ? 'Mengarahkan ke dasbor studio Anda...' : 'Routing you to your studio dashboard…'}</p>
              </div>
            ) : status === 'failed' ? (
              <div className="py-12 text-center">
                <div className="mx-auto grid size-12 place-items-center rounded-2xl bg-danger/15 text-danger">
                  <AlertCircle className="w-6 h-6" />
                </div>
                <p className="mt-3 text-sm font-medium text-danger">{language === 'id' ? 'Analisis terhenti.' : 'Analysis interrupted.'}</p>
              </div>
            ) : (
              <>
                {/* Realtime Waveform Matrix */}
                <div className="space-y-1.5 mb-5">
                  <div className="flex items-center justify-between text-[10px] font-mono text-text-muted">
                    <span className="flex items-center gap-1.5 text-accent-1">
                      <AudioLines className="w-3 h-3 animate-bounce" />
                      {language === 'id' ? 'FREKUENSI SINYAL ANALISIS' : 'AI SIGNAL FREQUENCY ANALYSIS'}
                    </span>
                    <span className="text-[10px] text-text-muted">9:16 VERTICAL RE-ENCODING</span>
                  </div>
                  <div className="flex h-24 items-end justify-between gap-1 rounded-xl bg-black/40 p-3 border border-border/40 shadow-inner">
                    {waveform.map((b, i) => (
                      <div
                        key={i}
                        className="flex-1 rounded-sm bg-gradient-to-t from-emerald-600 via-accent-1 to-emerald-300 transition-all duration-100 ease-in-out shadow-sm shadow-accent-1/20"
                        style={{ height: `${Math.max(12, b * 100)}%`, opacity: 0.35 + b * 0.65 }}
                      />
                    ))}
                  </div>
                </div>

                {/* AI Telemetry 4-Grid (No Fake Clip Bars) */}
                <div className="grid grid-cols-2 gap-2.5 mb-5">
                  <div className="rounded-xl border border-border/50 bg-card/40 p-2.5 flex flex-col justify-center">
                    <div className="flex items-center gap-1.5 text-[10px] text-text-muted mb-1">
                      <Brain className="w-3 h-3 text-accent-1" />
                      <span>{language === 'id' ? 'Model Analitik' : 'Analytical Model'}</span>
                    </div>
                    <span className="text-xs font-mono font-medium text-text-primary">Groq Llama 3.3 / Whisper</span>
                  </div>

                  <div className="rounded-xl border border-border/50 bg-card/40 p-2.5 flex flex-col justify-center">
                    <div className="flex items-center gap-1.5 text-[10px] text-text-muted mb-1">
                      <Scissors className="w-3 h-3 text-accent-1" />
                      <span>{language === 'id' ? 'Target Durasi' : 'Target Duration'}</span>
                    </div>
                    <span className="text-xs font-mono font-medium text-accent-1">25s – 75s (Viral Cut)</span>
                  </div>

                  <div className="rounded-xl border border-border/50 bg-card/40 p-2.5 flex flex-col justify-center">
                    <div className="flex items-center gap-1.5 text-[10px] text-text-muted mb-1">
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      <span>{language === 'id' ? 'Fokus Konten' : 'Content Focus'}</span>
                    </div>
                    <span className="text-xs font-medium text-text-primary">{language === 'id' ? 'Hook & Klimaks Emosi' : 'Hooks & Emotional Peaks'}</span>
                  </div>

                  <div className="rounded-xl border border-border/50 bg-card/40 p-2.5 flex flex-col justify-center">
                    <div className="flex items-center gap-1.5 text-[10px] text-text-muted mb-1">
                      <Video className="w-3 h-3 text-sky-400" />
                      <span>{language === 'id' ? 'Pelacak Wajah' : 'Face Tracking'}</span>
                    </div>
                    <span className="text-xs font-medium text-text-primary">{language === 'id' ? 'Aktif (9:16 Center Focus)' : 'Active (9:16 Center Focus)'}</span>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Live Terminal Status Box */}
          {status !== 'completed' && status !== 'failed' && (
            <div className="rounded-xl bg-black/60 border border-accent-1/30 p-3 font-mono text-[11px] shadow-inner space-y-1">
              <div className="flex items-center gap-2 text-accent-1/70 text-[10px] border-b border-border/30 pb-1">
                <AudioWaveform className="w-3 h-3 text-accent-1" />
                <span>AUVI_PIPELINE_LOGS // STAGE_{currentStep || 1}</span>
              </div>
              <div className="text-text-primary flex items-center gap-2 pt-0.5">
                <span className="text-accent-1 font-bold">&gt;</span>
                <span className="truncate">{translateMessage(message) || (language === 'id' ? 'Memproses analisis tensor...' : 'Processing tensor analysis...')}</span>
                <span className="w-1.5 h-3.5 bg-accent-1 inline-block animate-pulse ml-auto shrink-0" />
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
