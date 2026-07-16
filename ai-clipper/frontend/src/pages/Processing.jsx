import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2, AudioLines } from 'lucide-react';
import ProcessingSteps from '../components/ProcessingSteps';
import { subscribeToProgress, deleteJob, getJob } from '../lib/api';
import useClipStore from '../store/useClipStore';
import Logo from '../components/Logo';

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
      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-4 md:px-6 py-5 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Logo size={32} showWordmark={false} />
          <button
            onClick={() => navigate('/')}
            className="btn-secondary py-2 border-transparent hover:border-border"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back</span>
          </button>
        </div>

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

      {/* Source summary */}
      {jobInfo && (
        <div className="relative z-10 mx-auto w-full max-w-5xl px-4 md:px-6">
          <div className="mx-auto flex max-w-md items-center gap-3 rounded-xl border border-border bg-card/60 px-4 py-2.5 backdrop-blur">
            <div className="grid size-8 shrink-0 place-items-center rounded-md bg-surface text-text-muted">
              <AudioLines className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <p className="truncate text-xs font-medium text-text-primary">{jobInfo.title || 'Your video'}</p>
              <p className="truncate text-[11px] text-text-muted">
                {jobInfo.source_type === 'youtube' ? 'YouTube' : 'Upload'} · job {jobId?.slice(0, 8)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold text-accent-1">{processing.progress}%</p>
            </div>
          </div>
        </div>
      )}

      {/* The blurry placeholder thumbnail while downloading */}
      {jobInfo?.source_type === 'youtube' && processing.step === 1 && (
        <div className="relative z-10 mx-auto w-full max-w-xl px-4 mt-6">
          <div className="aspect-video bg-surface rounded-xl border border-border overflow-hidden relative shadow-2xl animate-pulse">
            <div className="absolute inset-0 flex items-center justify-center text-text-muted">
              Downloading from YouTube...
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="relative z-10 flex-grow flex flex-col items-center justify-center w-full px-4 md:px-6 py-10">
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
