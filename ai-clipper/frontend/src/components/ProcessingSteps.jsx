import React from 'react';
import { CloudDownload, AudioWaveform, Brain, Scissors, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Downloading', icon: CloudDownload },
  { id: 2, label: 'Transcribing', icon: AudioWaveform },
  { id: 3, label: 'Analyzing', icon: Brain },
  { id: 4, label: 'Generating Clips', icon: Scissors },
];

export default function ProcessingSteps({ currentStep, progress, message, status, error }) {
  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Steps Container */}
      <div className="relative flex justify-between mb-12">
        {/* Connecting Line Background */}
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-border -translate-y-1/2 rounded-full z-0"></div>
        
        {/* Active Connecting Line */}
        <div 
          className="absolute top-1/2 left-0 h-1 bg-gradient-to-r from-accent-1 to-accent-2 -translate-y-1/2 rounded-full z-0 transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, ((currentStep - 1) / (STEPS.length - 1)) * 100))}%` }}
        ></div>

        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id && status !== 'failed';
          const isCompleted = currentStep > step.id || status === 'completed';
          const isFailed = currentStep === step.id && status === 'failed';

          let bgColor = 'bg-surface border-border text-text-muted';
          if (isCompleted) bgColor = 'bg-success/20 border-success text-success';
          else if (isActive) bgColor = 'bg-accent-1/20 border-accent-1 text-accent-1 shadow-[0_0_15px_rgba(99,102,241,0.5)]';
          else if (isFailed) bgColor = 'bg-danger/20 border-danger text-danger';

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center">
              <div 
                className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${bgColor}`}
              >
                {isCompleted ? (
                  <CheckCircle className="w-6 h-6" />
                ) : isFailed ? (
                  <AlertCircle className="w-6 h-6" />
                ) : isActive ? (
                  <div className="relative flex items-center justify-center">
                    <Icon className="w-5 h-5 absolute" />
                    <Loader2 className="w-7 h-7 animate-spin opacity-30" />
                  </div>
                ) : (
                  <Icon className="w-5 h-5" />
                )}
              </div>
              <div className={`absolute top-14 text-sm font-medium whitespace-nowrap ${isActive || isCompleted ? 'text-text-primary' : 'text-text-muted'}`}>
                {step.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Status Card */}
      <div className={`card p-6 border ${status === 'failed' ? 'border-danger/50' : 'border-border'}`}>
        {status === 'failed' ? (
          <div className="flex items-start gap-4">
            <div className="p-3 bg-danger/10 rounded-full text-danger shrink-0">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-danger mb-1">Processing Failed</h3>
              <p className="text-text-muted">{error || 'An unexpected error occurred during processing.'}</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-end">
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-1">
                  {status === 'completed' ? 'Processing Complete!' : STEPS.find(s => s.id === currentStep)?.label || 'Preparing...'}
                </h3>
                <p className="text-sm text-text-muted">{message || 'Starting job...'}</p>
              </div>
              <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-1 to-accent-2">
                {progress}%
              </div>
            </div>
            
            <div className="progress-bar h-2">
              <div 
                className={`progress-bar-fill ${status === 'completed' ? 'bg-success' : ''}`}
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
