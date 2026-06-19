import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Filter, ArrowUpDown, Loader2 } from 'lucide-react';
import useClipStore from '../store/useClipStore';
import { getJob, getClips } from '../lib/api';

import VideoPlayer from '../components/VideoPlayer';
import ClipTimeline from '../components/ClipTimeline';
import ClipCard from '../components/ClipCard';
import ClipPreviewModal from '../components/ClipPreviewModal';

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
    setCurrentJob
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

  const originalVideoUrl = `/storage/jobs/${jobId}/original.mp4`;

  return (
    <div className="min-h-screen bg-base flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 h-16 border-b border-border bg-surface flex items-center justify-between px-4 sm:px-6 z-10">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="p-2 rounded-full hover:bg-border text-text-muted hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="h-6 w-px bg-border"></div>
          <div>
            <h1 className="text-sm font-bold text-text-primary line-clamp-1">{jobInfo?.title || 'Untitled Video'}</h1>
            <p className="text-xs text-text-muted">Generated {filteredClips.length} AI clips</p>
          </div>
        </div>
      </header>

      {/* Main Layout: 2 Columns */}
      <div className="flex-grow flex flex-col lg:flex-row overflow-hidden">
        
        {/* Left Column: Video Player (70%) */}
        <div className="w-full lg:w-[65%] xl:w-[70%] flex flex-col bg-base p-4 sm:p-6 overflow-y-auto border-r border-border">
          <div className="w-full max-w-5xl mx-auto flex flex-col gap-4">
            {/* Player */}
            <div className="shadow-2xl">
              <VideoPlayer 
                ref={playerRef}
                src={originalVideoUrl} 
                onTimeUpdate={setCurrentTime}
              />
            </div>
            
            {/* Timeline */}
            <div className="card p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-semibold text-text-primary">Clip Timeline Map</h3>
                <span className="text-xs text-text-muted">Click segment to seek</span>
              </div>
              <ClipTimeline 
                clips={useClipStore.getState().clips} // Pass all clips to timeline, not just filtered
                duration={jobInfo?.duration || 0}
                currentTime={currentTime}
                onSeek={handleSeek}
              />
            </div>
          </div>
        </div>

        {/* Right Column: Clips List (30%) */}
        <div className="w-full lg:w-[35%] xl:w-[30%] flex flex-col bg-surface overflow-hidden">
          
          {/* Filters Bar */}
          <div className="flex-shrink-0 p-4 border-b border-border bg-surface sticky top-0 z-10 space-y-3 shadow-md">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-text-muted" />
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
                        ? 'bg-accent-1 text-white' 
                        : 'bg-card text-text-muted hover:text-text-primary hover:bg-border'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-4 h-4 text-text-muted" />
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="flex-1 bg-card border border-border rounded py-1 px-2 text-xs text-text-primary outline-none focus:border-accent-1"
              >
                <option value="score">Sort by: Viral Score (High to Low)</option>
                <option value="duration">Sort by: Duration (Long to Short)</option>
                <option value="position">Sort by: Position in Video</option>
              </select>
            </div>
          </div>

          {/* Clips List */}
          <div className="flex-grow overflow-y-auto p-4 flex flex-col gap-4">
            {filteredClips.length === 0 ? (
              <div className="text-center p-8">
                <p className="text-text-muted">No clips match the current filter.</p>
              </div>
            ) : (
              filteredClips.map((clip) => (
                <div key={clip.id} className="animate-fade-in">
                  <ClipCard clip={clip} />
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      <ClipPreviewModal />
    </div>
  );
}
