import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Youtube, Settings as SettingsIcon, CheckCircle2, AlertCircle } from 'lucide-react';
import PreferencesModal from '../components/PreferencesModal';
import Logo from '../components/Logo';
import useClipStore from '../store/useClipStore';

export default function Integrations() {
  const { language } = useClipStore();
  const [status, setStatus] = useState({ linked: false, channel_name: null });
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/youtube/status')
      .then(res => res.json())
      .then(data => {
        setStatus(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleConnect = () => {
    window.location.href = 'http://localhost:8000/api/youtube/login';
  };

  const handleDisconnect = () => {
    fetch('http://localhost:8000/api/youtube/disconnect', { method: 'POST' })
      .then(() => setStatus({ linked: false, channel_name: null }));
  };

  return (
    <div className="min-h-screen bg-base text-text-primary font-sans flex flex-col transition-colors duration-300">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full bg-base/80 backdrop-blur-md border-b border-border">
        <div className="w-full max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3">
            <Logo size={32} showWordmark={true} />
          </Link>
          
          <div className="flex items-center gap-5 ml-auto">
            <Link to="/" className="text-[14px] font-medium text-text-primary hover:text-accent-1 transition-colors">
              {language === 'id' ? 'Beranda' : 'Home'}
            </Link>
            <Link to="/dashboard" className="text-[14px] font-medium text-text-primary hover:text-accent-1 transition-colors">
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center w-full max-w-3xl mx-auto px-4 pt-16 pb-16">
        <div className="w-full text-left mb-10">
          <h1 className="text-[40px] md:text-[48px] font-serif text-text-primary leading-[1.1] tracking-tight mb-4">
            {language === 'id' ? 'Integrasi' : 'Integrations'}
          </h1>
          <p className="text-text-muted text-[17px] font-normal">
            {language === 'id' 
              ? 'Hubungkan akun Anda untuk mengotomatiskan alur kerja pemotongan dan publikasi.' 
              : 'Connect your accounts to automate the clipping and publishing workflow.'}
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-emerald-600"></div>
          </div>
        ) : (
          <div className="w-full bg-card rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-border p-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 shrink-0 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 border border-red-500/20">
                  <Youtube className="w-7 h-7" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-text-primary tracking-tight">YouTube Webhooks & Shorts</h2>
                  <p className="text-text-muted text-[15px] mt-1 max-w-md leading-relaxed">
                    {language === 'id' 
                      ? 'Otomatis proses podcast YouTube panjang baru Anda dan publikasikan klip langsung ke Shorts.'
                      : 'Automatically process your new long-form YouTube podcasts and publish clips directly to Shorts.'}
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col md:items-end gap-3 shrink-0">
                {status.linked ? (
                  <>
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm font-medium border border-emerald-100">
                      <CheckCircle2 className="w-4 h-4" />
                      {status.channel_name}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => setIsModalOpen(true)}
                        className="px-4 py-2 bg-base border border-border text-text-primary text-sm font-medium rounded-xl hover:bg-card-hover transition-colors flex items-center gap-2"
                      >
                        <SettingsIcon className="w-4 h-4" />
                        {language === 'id' ? 'Konfigurasi Gaya' : 'Configure Style'}
                      </button>
                      <button 
                        onClick={handleDisconnect}
                        className="px-4 py-2 text-red-500 text-sm font-medium rounded-xl hover:bg-red-500/10 transition-colors"
                      >
                        {language === 'id' ? 'Putuskan' : 'Disconnect'}
                      </button>
                    </div>
                  </>
                ) : (
                  <button
                    onClick={handleConnect}
                    className="px-6 py-2.5 bg-accent-1 text-white text-[15px] font-semibold rounded-xl hover:bg-accent-2 transition-colors shadow-sm"
                  >
                    {language === 'id' ? 'Hubungkan YouTube' : 'Connect YouTube'}
                  </button>
                )}
              </div>

            </div>

            {status.linked && (
              <div className="mt-8 pt-6 border-t border-slate-100">
                <div className="flex items-start gap-3 bg-amber-50 p-4 rounded-xl border border-amber-100/50">
                  <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-[14px] text-amber-800 leading-relaxed">
                    <strong>Webhook is active!</strong> Any new video uploaded to <em>{status.channel_name}</em> will automatically be processed using your configured style settings and sent to your Drafts.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <PreferencesModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}
