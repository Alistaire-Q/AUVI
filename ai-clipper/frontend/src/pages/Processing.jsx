import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import ProcessingSteps from '../components/ProcessingSteps';
import { subscribeToProgress, deleteJob, getJob } from '../lib/api';
import useClipStore from '../store/useClipStore';

export default function Processing() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { processing, setProcessing, resetProcessing, addRecentProject } = useClipStore();
  const [jobInfo, setJobInfo] = useState(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (!jobId) {
      navigate('/');
      return;
    }

    // Fetch initial job info
    getJob(jobId).then(data => {
      setJobInfo(data);
      // Update judul di Recent Projects jika sudah tersedia
      if (data.title && data.title !== 'Untitled') {
        addRecentProject({
          id: jobId,
          title: data.title,
          source: data.source_type || 'youtube',
          date: data.created_at || new Date().toISOString(),
        });
      }
      if (data.status === 'completed') {
        navigate(`/dashboard/${jobId}`);
      }
    }).catch(err => {
      console.error("Failed to get job:", err);
    });

    // Subscribe to SSE for real-time progress
    const eventSource = subscribeToProgress(jobId, {
      onProgress: (data) => {
        setProcessing({
          step: data.step,
          progress: data.progress,
          message: data.message,
          status: data.status,
          error: null,
        });
      },
      onComplete: (data) => {
        setProcessing({
          step: data.step,
          progress: 100,
          message: data.message || 'Complete',
          status: 'completed',
          error: null,
        });
        
        // Short delay for the user to see 100% completion before redirecting
        setTimeout(() => {
          navigate(`/dashboard/${jobId}`);
        }, 1500);
      },
      onError: (errorMsg) => {
        setProcessing({
          status: 'failed',
          error: errorMsg,
        });
      }
    });

    return () => {
      eventSource.close();
      resetProcessing();
    };
  }, [jobId, navigate, setProcessing, resetProcessing]);

  const handleCancel = async () => {
    if (confirm('Are you sure you want to cancel processing? This cannot be undone.')) {
      setCancelling(true);
      try {
        await deleteJob(jobId);
        navigate('/');
      } catch (err) {
        alert('Failed to cancel job: ' + (err.response?.data?.detail || err.message));
        setCancelling(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-base relative flex flex-col">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-accent-1/5 to-transparent pointer-events-none"></div>

      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
        <button 
          onClick={() => navigate('/')}
          className="btn-secondary py-2 border-transparent hover:border-border"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>
        
        {processing.status !== 'completed' && processing.status !== 'failed' && (
          <button 
            onClick={handleCancel}
            disabled={cancelling}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-danger hover:bg-danger/10 transition-colors text-sm font-medium"
          >
            <Trash2 className="w-4 h-4" />
            <span>{cancelling ? 'Cancelling...' : 'Cancel'}</span>
          </button>
        )}
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-grow flex flex-col items-center justify-center w-full max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-16 animate-fade-in">
          <h1 className="text-3xl font-bold text-text-primary mb-3">
            {processing.status === 'failed' ? 'Processing Failed' : 'Analyzing Video...'}
          </h1>
          <p className="text-text-muted">
            {jobInfo?.title || 'Your video'} is being processed by AUVI.
          </p>
        </div>

        {/* The blurry placeholder thumbnail */}
        {jobInfo?.source_type === 'youtube' && processing.step === 1 && (
          <div className="w-full max-w-xl mx-auto mb-12 aspect-video bg-surface rounded-xl border border-border overflow-hidden relative shadow-2xl animate-pulse">
             <div className="absolute inset-0 flex items-center justify-center text-text-muted">
               Downloading from YouTube...
             </div>
          </div>
        )}

        {/* Stepper component receives the global processing state */}
        <ProcessingSteps 
          currentStep={processing.step}
          progress={processing.progress}
          message={processing.message}
          status={processing.status}
          error={processing.error}
        />
      </main>
    </div>
  );
}
