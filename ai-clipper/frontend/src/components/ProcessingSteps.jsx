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
  return (
    <div className="w-full max-w-3xl mx-auto">
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

      {/* Steps list */}
      <div className="mt-8 grid gap-4">
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

      </div>
    </div>
  );
}
