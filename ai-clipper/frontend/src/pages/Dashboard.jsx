import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Filter, ArrowUpDown, Loader2, Sparkles, Download, CheckCircle2, Clock, Hash, Captions } from 'lucide-react';
import useClipStore from '../store/useClipStore';
import { getJob, getClips } from '../lib/api';

import VideoPlayer from '../components/VideoPlayer';
import ClipTimeline from '../components/ClipTimeline';
import ClipCard from '../components/ClipCard';
import ClipPreviewModal from '../components/ClipPreviewModal';
import Logo from '../components/Logo';

export default function Dashboard() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const playerRef = useRef(null);

  const [jobInfo, setJobInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);

  const {
    setClips,
    getFilteredClips,
    filter,
    setFilter,
    sortBy,
    setSortBy,
    setCurrentJob,
  } = useClipStore();

  useEffect(() => {
    if (!jobId) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const job = await getJob(jobId);
        if (job.status !== 'completed') {
          // If not completed, send back to processing or home
          if (job.status === 'pending' || job.step > 0) {
            navigate(`/processing/${jobId}`);
          } else {
            setError(`Job status is ${job.status}`);
          }
          return;
        }

        setJobInfo(job);
        setCurrentJob(job);

        const clipsData = await getClips(jobId);
        setClips(clipsData);

      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load job data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [jobId, navigate, setClips, setCurrentJob]);

  const handleSeek = (time) => {
    if (playerRef.current) {
      playerRef.current.seekTo(time);
      playerRef.current.play();
    }
  };

  const filteredClips = getFilteredClips();
  const allClips = useClipStore.getState().clips;

  const avgScore = filteredClips.length
    ? Math.round(filteredClips.reduce((s, c) => s + c.score, 0) / filteredClips.length)
    : 0;
  const topScore = filteredClips.length
    ? Math.max(...filteredClips.map((c) => c.score))
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-base flex flex-col items-center justify-center">
        <Loader2 className="w-12 h-12 text-accent-1 animate-spin mb-4" />
        <p className="text-text-primary font-medium">Loading clips...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-base flex flex-col items-center justify-center p-6 text-center">
        <div className="p-4 bg-danger/10 text-danger rounded-xl mb-4 max-w-md w-full border border-danger/20">
          <h2 className="text-lg font-bold mb-1">Error Loading Dashboard</h2>
          <p className="text-sm">{error}</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/')}>
          Return Home
        </button>
      </div>
    );
  }

  const originalVideoUrl = `/api/jobs/${jobId}/video`;

  return (
    <div className="min-h-screen bg-base flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 h-16 border-b border-border bg-surface/80 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6 z-10">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg hover:bg-card text-text-muted hover:text-text-primary transition-colors flex items-center gap-1.5"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="h-6 w-px bg-border"></div>
          <div className="flex items-center gap-2">
            <Logo size={26} showWordmark={false} />
            <div>
              <h1 className="text-sm font-semibold text-text-primary line-clamp-1">{jobInfo?.title || 'Untitled Video'}</h1>
              <p className="text-xs text-text-muted">{filteredClips.length} AI clips generated</p>
            </div>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-card/60 px-2.5 py-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-success" />
            <span className="text-xs font-medium text-text-primary">Analyzed</span>
          </div>
        </div>
      </header>

      {/* Main Layout: 2 Columns */}
      <div className="flex-grow flex flex-col lg:flex-row overflow-hidden">

        {/* Left Column: Video Player + Timeline */}
        <div className="w-full lg:w-[60%] xl:w-[65%] flex flex-col bg-base p-4 sm:p-6 overflow-y-auto border-r border-border">
          <div className="w-full max-w-5xl mx-auto flex flex-col gap-4">
            {/* Summary stats */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-3 gap-3"
            >
              {[
                { label: 'Avg score', value: avgScore },
                { label: 'Top clip', value: topScore },
                { label: 'Ready', value: filteredClips.length },
              ].map((s) => (
                <div key={s.label} className="rounded-xl border border-border bg-card/60 px-3 py-2 backdrop-blur">
                  <p className="text-[10px] uppercase tracking-wider text-text-muted">{s.label}</p>
                  <p className="text-xl font-semibold md:text-2xl"><span className="auvi-gradient-text">{s.value}</span></p>
                </div>
              ))}
            </motion.div>

            {/* Feature highlights */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { icon: Sparkles, label: 'Clips', value: `${filteredClips.length} found` },
                { icon: Captions, label: 'Captions', value: 'Auto' },
                { icon: Clock, label: 'Reframe', value: '9:16' },
                { icon: Hash, label: 'Hashtags', value: `${filteredClips.length * 2} auto` },
              ].map((f) => (
                <div key={f.label} className="flex items-center gap-2 rounded-xl border border-border bg-card/40 px-3 py-2 backdrop-blur">
                  <div className="grid size-7 place-items-center rounded-lg bg-accent-1/15 text-accent-1">
                    <f.icon className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-text-muted">{f.label}</p>
                    <p className="text-xs font-medium text-text-primary">{f.value}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Player */}
            <div className="rounded-xl overflow-hidden shadow-sm border border-border bg-card">
              <VideoPlayer
                ref={playerRef}
                src={originalVideoUrl}
                defaultDuration={jobInfo?.duration || 0}
                onTimeUpdate={setCurrentTime}
              />
            </div>

            {/* Timeline */}
            <div className="card p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-semibold text-text-primary">Clip timeline map</h3>
                <span className="text-xs text-text-muted">Click segment to seek</span>
              </div>
              <ClipTimeline
                clips={allClips} // Pass all clips to timeline, not just filtered
                duration={jobInfo?.duration || 0}
                currentTime={currentTime}
                onSeek={handleSeek}
              />
            </div>
          </div>
        </div>

        {/* Right Column: Clips List */}
        <div className="w-full lg:w-[40%] xl:w-[35%] flex flex-col bg-surface overflow-hidden border-l border-border">

          {/* Filters Bar */}
          <div className="flex-shrink-0 p-4 border-b border-border bg-card sticky top-0 z-10 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 text-sm font-medium text-text-primary">
                <Sparkles className="w-4 h-4 text-accent-1" />
                Your clips
                <span className="rounded-full bg-surface px-2 py-0.5 text-[11px] text-text-muted border border-border">{filteredClips.length}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-text-muted shrink-0" />
              <div className="flex flex-wrap gap-1 flex-1">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'high', label: 'Viral (>70%)' },
                  { id: 'medium', label: 'Good (40-70%)' },
                  { id: 'short', label: '< 30s' },
                ].map(f => (
                  <button
                    key={f.id}
                    onClick={() => setFilter(f.id)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      filter === f.id
                        ? 'bg-slate-900 text-white'
                        : 'bg-card text-text-muted hover:text-text-primary hover:border-slate-300 border border-border'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-4 h-4 text-text-muted shrink-0" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="flex-1 bg-card border border-border rounded-lg py-1.5 px-2 text-xs text-text-primary outline-none focus:border-accent-1"
              >
                <option value="score">Sort by: Viral Score (High to Low)</option>
                <option value="duration">Sort by: Duration (Long to Short)</option>
                <option value="position">Sort by: Position in Video</option>
              </select>
            </div>
          </div>

          {/* Clips Grid */}
          <div className="flex-grow overflow-y-auto p-4">
            {filteredClips.length === 0 ? (
              <div className="text-center p-8">
                <p className="text-text-muted">No clips match the current filter.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 gap-4">
                {filteredClips.map((clip, i) => (
                  <ClipCard key={clip.id} clip={clip} index={i} />
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

      <ClipPreviewModal />
    </div>
  );
}
