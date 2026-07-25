import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Settings, Link2, Upload, PlaySquare, Video, ArrowRight, Sparkles, Youtube } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import SettingsDrawer from '../components/SettingsDrawer';
import GenerateOptionsModal from '../components/GenerateOptionsModal';
import useClipStore from '../store/useClipStore';
import { processUrl, uploadFile, getJobs } from '../lib/api';

export default function Home() {
  const { toggleSettings, setUploadProgress, language } = useClipStore();
  const [recentProjects, setRecentProjects] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getJobs()
      .then(jobs => {
        // Map backend jobs to match expected format
        const formatted = jobs.map(j => ({
          id: j.id,
          title: j.title || j.url || 'Untitled Video',
          source: j.source_type || 'youtube',
          date: j.created_at,
          status: j.status
        }));
        setRecentProjects(formatted);
      })
      .catch(err => console.error("Failed to load jobs:", err));
  }, []);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingVideo, setPendingVideo] = useState(null); // { type: 'link' | 'upload', data: string | File }
  const [isLoading, setIsLoading] = useState(false);
  const [modalUploadProgress, setModalUploadProgress] = useState(0);

  const [urlInput, setUrlInput] = useState('');
  const fileInputRef = useRef(null);

  const handleVideoInput = (type, data) => {
    setPendingVideo({ type, data });
    setIsModalOpen(true);
  };

  const handleGenerate = async () => {
    if (!pendingVideo) return;
    setIsLoading(true);
    setModalUploadProgress(0);

    try {
      if (pendingVideo.type === 'link') {
        const url = pendingVideo.data;
        const currentSettings = useClipStore.getState().settings;
        const result = await processUrl(url, currentSettings);

        let videoTitle = url;
        try {
          const { getJob } = await import('../lib/api');
          const jobInfo = await getJob(result.job_id);
          if (jobInfo.title && jobInfo.title !== 'Untitled') {
            videoTitle = jobInfo.title;
          }
        } catch { }

        navigate(`/processing/${result.job_id}`);
      } else if (pendingVideo.type === 'upload') {
        const file = pendingVideo.data;
        const currentSettings = useClipStore.getState().settings;
        const result = await uploadFile(file, currentSettings, (percent) => {
          setModalUploadProgress(percent);
          setUploadProgress(percent);
        });

        navigate(`/processing/${result.job_id}`);
      }
    } catch (err) {
      console.error("Failed to generate:", err);
    } finally {
      setIsLoading(false);
      setIsModalOpen(false);
      setPendingVideo(null);
    }
  };

  const onContinueClick = () => {
    if (urlInput.trim()) {
      handleVideoInput('link', urlInput.trim());
    }
  };

  const onFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleVideoInput('upload', files[0]);
    }
    e.target.value = '';
  };

  return (
    <div className="min-h-screen bg-base text-text-primary font-sans flex flex-col transition-colors duration-300">
      <header className="sticky top-0 z-50 w-full bg-base/80 backdrop-blur-md border-b border-border">
        <div className="w-full max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-text-primary rounded-lg flex items-center justify-center text-base font-bold text-sm tracking-tighter">
              A
            </div>
            <span className="font-bold text-base tracking-wide text-text-primary">AUVI</span>
          </div>
          
          <div className="flex items-center gap-6 ml-auto">
            <nav className="hidden md:flex items-center gap-6 text-[14px] font-medium text-text-primary">
              <a href="#" className="hover:text-accent-1 transition-colors">{language === 'id' ? 'Ruang Kerja' : 'Workspace'}</a>
            </nav>
            <div className="hidden sm:block w-px h-4 bg-border"></div>
            <Link to="/projects" className="text-[14px] font-medium text-text-primary hover:text-accent-1 transition-colors hidden sm:block">
              {language === 'id' ? 'Proyek Saya' : 'My projects'}
            </Link>
            <Link to="/integrations" className="text-[14px] font-medium text-text-primary hover:text-accent-1 transition-colors hidden sm:block">
              {language === 'id' ? 'Integrasi' : 'Integrations'}
            </Link>
            <button
              onClick={toggleSettings}
              className="flex items-center gap-2 px-3 py-1.5 ml-2 rounded-full border border-border text-[13px] font-medium hover:bg-card-hover transition-colors text-text-primary bg-card shadow-sm"
            >
              <Settings className="w-[14px] h-[14px]" />
              {language === 'id' ? 'Pengaturan' : 'Settings'}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-grow flex flex-col items-center w-full max-w-4xl mx-auto px-4 pt-20 pb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 bg-white text-[10px] font-bold text-slate-500 tracking-[0.15em] mb-10 shadow-sm uppercase">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-600"></div>
          LOCAL · PRIVATE · READY-TO-POST
        </div>

        <div className="w-full flex flex-col items-center">
          <h1 className="text-center text-[52px] md:text-[68px] font-serif text-text-primary leading-[1.1] mb-6 max-w-[800px] tracking-tight">
            {language === 'id' ? 'Ubah video panjang menjadi' : 'Turn long videos into'}<br/>
            <span className="bg-[#e8f5e9] px-2 py-1 mx-1 text-[#1a1f2e]">
              {language === 'id' ? 'klip pendek' : 'short clips'}
            </span> {language === 'id' ? 'siap tayang' : 'ready to ship'}
          </h1>
          <p className="text-center text-text-muted text-[17px] md:text-[19px] max-w-2xl mb-12 font-normal leading-relaxed">
            {language === 'id' 
              ? 'Tempel tautan YouTube atau unggah file. AUVI menemukan momen terbaik, menilai potensi viral, dan mengekspor klip vertikal dengan takarir.'
              : 'Paste a YouTube link or upload a file. AUVI finds the strongest moments, scores virality, and exports vertical clips with captions.'}
          </p>
        </div>

        {/* Input Bar */}
        <div className="w-full max-w-[800px] bg-card rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-2.5 flex items-center border border-border mb-16">
          <div className="pl-4 pr-3 text-text-hint">
            <Link2 className="w-[22px] h-[22px]" />
          </div>
          <input 
            type="text" 
            placeholder={language === 'id' ? 'Tempel tautan video di sini...' : 'Paste video link here...'}
            className="flex-grow bg-transparent border-none outline-none text-text-primary placeholder-text-hint text-[17px] py-3.5"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onContinueClick();
            }}
          />
          <div className="flex items-center gap-2 pr-1">
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".mp4,.mov,.avi,.webm"
              onChange={onFileChange}
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-5 py-3 rounded-xl border border-border text-[15px] font-semibold hover:bg-card-hover transition-colors whitespace-nowrap text-text-primary"
            >
              <Upload className="w-[18px] h-[18px]" />
              {language === 'id' ? 'Unggah File' : 'Upload File'}
            </button>
            <button 
              onClick={onContinueClick}
              className="px-8 py-3 rounded-xl bg-text-primary text-[var(--bg-base)] text-[15px] font-semibold hover:bg-text-muted transition-colors whitespace-nowrap"
            >
              {language === 'id' ? 'Lanjutkan' : 'Continue'}
            </button>
          </div>
        </div>

        {/* Clip workspace placeholder */}
        <div className="w-full max-w-[850px] bg-card rounded-[32px] shadow-[0_8px_40px_rgb(0,0,0,0.03)] border border-border p-8 text-left relative overflow-hidden">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-[22px] font-semibold text-text-primary mb-1.5 tracking-tight">{language === 'id' ? 'Ruang kerja klip' : 'Clip workspace'}</h2>
              <p className="text-text-muted text-[15px]">{language === 'id' ? 'Sesuaikan keluaran sebelum AUVI memproses.' : 'Tune output before AUVI runs the pipeline.'}</p>
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-border text-[13px] font-medium text-text-muted bg-card">
              <div className="w-2 h-2 rounded-full bg-border"></div>
              {language === 'id' ? 'Belum ada sumber' : 'No source yet'}
            </div>
          </div>
          
          <div className="mt-8 bg-surface rounded-2xl h-48 border border-border flex items-center justify-center">
             <div className="text-center text-text-hint">
               <p className="text-[15px] font-medium">{language === 'id' ? 'Menunggu masukan video...' : 'Waiting for video input...'}</p>
             </div>
          </div>
        </div>

        {/* Recent Projects (if any) */}
        {recentProjects.length > 0 && (
          <section className="mt-20 w-full max-w-[850px]">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-text-primary mb-2">{language === 'id' ? 'Proyek Anda' : 'Your Projects'}</h3>
              <p className="text-text-muted text-[15px]">{language === 'id' ? 'Kelola dan lihat video yang Anda proses sebelumnya.' : 'Manage and view your previously processed videos.'}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {recentProjects.map((project) => (
                <Link 
                  to={`/dashboard/${project.id}`} 
                  key={project.id}
                  className="group flex flex-col bg-card border border-border rounded-2xl p-5 hover:shadow-xl hover:border-accent-1/30 transition-all duration-300 transform hover:-translate-y-1"
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-accent-1/10 flex items-center justify-center text-accent-1 shrink-0 group-hover:scale-110 transition-transform duration-300">
                      {project.source === 'youtube' ? <Youtube className="w-5 h-5" /> : <PlaySquare className="w-5 h-5" />}
                    </div>
                    <div className="min-w-0 flex-1 overflow-hidden">
                      <p className="text-sm font-medium text-text-primary truncate" title={project.title}>
                          {project.title && project.title.startsWith('http') 
                            ? (project.title.includes('v=') ? `YouTube Video (${project.title.split('v=')[1].substring(0, 11)})` : (project.title.includes('youtu.be/') ? `YouTube Video (${project.title.split('youtu.be/')[1].substring(0, 11)})` : 'YouTube Video')) 
                            : project.title}
                      </p>
                      <p className="mt-1 text-xs text-text-muted flex items-center gap-2">
                        {new Date(project.date).toLocaleDateString()}
                        {project.status === 'pending' || project.status === 'downloading' || project.status === 'analyzing' || project.status === 'clipping' || project.status === 'transcribing' ? (
                             <span className="text-amber-600 font-semibold">• Processing</span>
                          ) : project.status === 'failed' ? (
                             <span className="text-red-500 font-semibold">• Failed</span>
                          ) : project.status === 'completed' && project.source === 'webhook' ? (
                             <span className="text-emerald-600 font-semibold flex items-center gap-1"><Sparkles className="w-3 h-3"/> Auto Draft</span>
                          ) : null}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-auto pt-4 border-t border-border flex items-center justify-between">
                    <span className="text-[13px] font-medium text-accent-1 group-hover:text-accent-2 flex items-center gap-1 transition-colors">
                      {language === 'id' ? 'Lihat Klip' : 'View Clips'} <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>

      <SettingsDrawer />

      <GenerateOptionsModal
        isOpen={isModalOpen}
        onClose={() => !isLoading && setIsModalOpen(false)}
        onGenerate={handleGenerate}
        isLoading={isLoading}
        pendingType={pendingVideo?.type}
        uploadProgress={modalUploadProgress}
      />
    </div>
  );
}
