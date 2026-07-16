import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Settings, Link2, Upload, PlaySquare, Video, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import SettingsDrawer from '../components/SettingsDrawer';
import GenerateOptionsModal from '../components/GenerateOptionsModal';
import useClipStore from '../store/useClipStore';
import { processUrl, uploadFile } from '../lib/api';

export default function Home() {
  const { toggleSettings, getRecentProjects, addRecentProject, setUploadProgress } = useClipStore();
  const recentProjects = getRecentProjects();
  const navigate = useNavigate();

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

        addRecentProject({
          id: result.job_id,
          title: videoTitle,
          source: 'youtube',
          date: new Date().toISOString(),
        });

        navigate(`/processing/${result.job_id}`);
      } else if (pendingVideo.type === 'upload') {
        const file = pendingVideo.data;
        const currentSettings = useClipStore.getState().settings;
        const result = await uploadFile(file, currentSettings, (percent) => {
          setModalUploadProgress(percent);
          setUploadProgress(percent);
        });

        addRecentProject({
          id: result.job_id,
          title: file.name,
          source: 'upload',
          date: new Date().toISOString(),
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
    <div className="min-h-screen bg-[#F8F9FA] text-slate-900 font-sans flex flex-col items-center">
      <header className="w-full max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-[#1a1f2e] rounded-[8px] flex items-center justify-center text-white font-bold text-lg">
            A
          </div>
          <span className="font-bold text-lg tracking-wide text-[#1a1f2e]">AUVI</span>
        </div>
        
        <nav className="hidden md:flex items-center gap-10 text-[15px] font-medium text-slate-500">
          <a href="#" className="hover:text-slate-900 transition-colors">Workspace</a>
          <a href="#" className="hover:text-slate-900 transition-colors">How it works</a>
        </nav>

        <div className="flex items-center gap-6">
          <Link to="/projects" className="text-[15px] font-medium text-slate-500 hover:text-slate-900 transition-colors hidden sm:block">
            My projects
          </Link>
          <button
            onClick={toggleSettings}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 text-[15px] font-medium hover:bg-slate-50 transition-colors text-slate-700 bg-white shadow-sm"
          >
            <Settings className="w-[18px] h-[18px]" />
            Settings
          </button>
        </div>
      </header>

      <main className="flex-grow flex flex-col items-center w-full max-w-4xl mx-auto px-4 pt-20 pb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 bg-white text-[10px] font-bold text-slate-500 tracking-[0.15em] mb-10 shadow-sm uppercase">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-600"></div>
          LOCAL · PRIVATE · READY-TO-POST
        </div>

        <h1 className="text-center text-[52px] md:text-[68px] font-serif text-[#1a1f2e] leading-[1.1] mb-6 max-w-[800px] tracking-tight">
          Turn long videos into<br/>
          <span className="bg-[#e8f5e9] px-2 py-1 mx-1 text-[#1a1f2e]">short clips</span> ready to ship
        </h1>

        <p className="text-center text-slate-500 text-[17px] md:text-[19px] max-w-2xl mb-12 font-normal leading-relaxed">
          Paste a YouTube link or upload a file. AUVI finds the strongest moments, scores virality, and exports vertical clips with captions.
        </p>

        {/* Input Bar */}
        <div className="w-full max-w-[800px] bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-2.5 flex items-center border border-slate-100 mb-16">
          <div className="pl-4 pr-3 text-slate-400">
            <Link2 className="w-[22px] h-[22px]" />
          </div>
          <input 
            type="text" 
            placeholder="Paste video link here..." 
            className="flex-grow bg-transparent border-none outline-none text-slate-700 placeholder-slate-400 text-[17px] py-3.5"
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
              className="flex items-center gap-2 px-5 py-3 rounded-xl border border-slate-200 text-[15px] font-semibold hover:bg-slate-50 transition-colors whitespace-nowrap text-slate-700"
            >
              <Upload className="w-[18px] h-[18px]" />
              Upload File
            </button>
            <button 
              onClick={onContinueClick}
              className="px-8 py-3 rounded-xl bg-[#0a1128] text-white text-[15px] font-semibold hover:bg-slate-800 transition-colors whitespace-nowrap"
            >
              Continue
            </button>
          </div>
        </div>

        {/* Clip workspace placeholder */}
        <div className="w-full max-w-[850px] bg-white rounded-[32px] shadow-[0_8px_40px_rgb(0,0,0,0.03)] border border-slate-100 p-8 text-left relative overflow-hidden">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-[22px] font-semibold text-[#1a1f2e] mb-1.5 tracking-tight">Clip workspace</h2>
              <p className="text-slate-500 text-[15px]">Tune output before AUVI runs the pipeline.</p>
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-slate-200 text-[13px] font-medium text-slate-500 bg-white">
              <div className="w-2 h-2 rounded-full bg-slate-200"></div>
              No source yet
            </div>
          </div>
          
          <div className="mt-8 bg-slate-50/50 rounded-2xl h-48 border border-slate-100 flex items-center justify-center">
             <div className="text-center text-slate-400">
               <p className="text-[15px] font-medium">Waiting for video input...</p>
             </div>
          </div>
        </div>

        {/* Recent Projects (if any) */}
        {recentProjects.length > 0 && (
          <section className="mt-20 w-full max-w-[850px]">
            <div className="mb-6 flex items-end justify-between">
              <div>
                <h2 className="text-[20px] font-semibold tracking-tight text-[#1a1f2e] flex items-center gap-2">
                  <PlaySquare className="w-5 h-5 text-emerald-600" />
                  Recent projects
                </h2>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {recentProjects.map((project, i) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                >
                  <Link
                    to={`/dashboard/${project.id}`}
                    className="group block h-full p-4 text-left transition-all hover:border-slate-300 rounded-2xl border border-slate-200 bg-white hover:shadow-md"
                  >
                    <div className="flex items-start gap-3">
                      <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-emerald-50 text-emerald-600">
                        {project.source === 'youtube' ? <Video className="w-4 h-4" /> : <PlaySquare className="w-4 h-4" />}
                      </div>
                      <div className="min-w-0 flex-1 overflow-hidden">
                        <p className="text-sm font-medium text-slate-900 truncate" title={project.title}>
                          {project.title}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {new Date(project.date).toLocaleDateString()}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                  </Link>
                </motion.div>
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
