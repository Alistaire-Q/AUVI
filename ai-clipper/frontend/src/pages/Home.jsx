import React, { useEffect } from 'react';
import { Settings, Sparkles, Video, PlaySquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import YouTubeInput from '../components/YouTubeInput';
import SettingsDrawer from '../components/SettingsDrawer';
import useClipStore from '../store/useClipStore';

export default function Home() {
  const { toggleSettings, getRecentProjects } = useClipStore();
  const recentProjects = getRecentProjects();

  return (
    <div className="min-h-screen bg-base relative overflow-hidden flex flex-col">
      {/* Background Decor */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-accent-1/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-accent-2/20 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-1 to-accent-2 flex items-center justify-center shadow-lg shadow-accent-1/20">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">AUVI</span>
        </div>
        <button 
          onClick={toggleSettings}
          className="p-2 rounded-full hover:bg-surface border border-transparent hover:border-border text-text-muted hover:text-white transition-all flex items-center gap-2"
        >
          <Settings className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline-block">Settings</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-grow flex flex-col items-center justify-center w-full max-w-4xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-slide-up">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-1/10 border border-accent-1/20 text-accent-1 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            <span>100% Free & Local Processing</span>
          </div>
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-text-muted mb-6 tracking-tight leading-tight">
            Turn long videos into <br />
            <span className="text-gradient">viral short clips</span>
          </h1>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Upload your video or paste a YouTube link. Our AI will analyze the content,
            find the most engaging moments, and generate ready-to-post vertical clips with captions.
          </p>
        </div>

        {/* Input Section */}
        <div className="w-full space-y-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="glass-panel rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-1 to-accent-2"></div>
            
            {/* Format Badges */}
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {['MP4', 'MOV', 'AVI', 'WebM', 'YouTube URL'].map((format) => (
                <span key={format} className="px-3 py-1 rounded-full bg-surface border border-border text-xs font-medium text-text-muted">
                  {format}
                </span>
              ))}
            </div>

            <div className="flex flex-col gap-8">
              <YouTubeInput />
              
              <div className="relative flex items-center justify-center">
                <div className="absolute w-full h-px bg-border"></div>
                <span className="relative bg-surface px-4 text-sm font-medium text-text-hint">OR</span>
              </div>
              
              <UploadZone />
            </div>
          </div>
        </div>

        {/* Recent Projects (if any) */}
        {recentProjects.length > 0 && (
          <div className="w-full mt-16 animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              <PlaySquare className="w-5 h-5 text-accent-1" />
              Recent Projects
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {recentProjects.map((project) => (
                <Link 
                  key={project.id} 
                  to={`/dashboard/${project.id}`}
                  className="card p-4 flex items-start gap-3 hover:border-accent-1/50 transition-all"
                >
                  <div className="p-2 bg-surface rounded-lg text-accent-2">
                    {project.source === 'youtube' ? <Video className="w-5 h-5" /> : <PlaySquare className="w-5 h-5" />}
                  </div>
                  <div className="overflow-hidden">
                    <p className="text-sm font-medium text-text-primary truncate" title={project.title}>
                      {project.title}
                    </p>
                    <p className="text-xs text-text-muted mt-1">
                      {new Date(project.date).toLocaleDateString()}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>

      <SettingsDrawer />
    </div>
  );
}
