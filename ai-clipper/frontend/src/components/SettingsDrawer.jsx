import React, { useEffect, useState } from 'react';
import { X, Settings2, Moon, Sun, Languages } from 'lucide-react';
import useClipStore from '../store/useClipStore';

export default function SettingsDrawer() {
  const { settingsOpen, closeSettings, language, setLanguage } = useClipStore();
  const [isDarkMode, setIsDarkMode] = useState(
    document.documentElement.classList.contains('dark')
  );

  // If closed, translate it off screen
  const translateX = settingsOpen ? 'translate-x-0' : 'translate-x-full';

  // Toggle Dark Mode
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          settingsOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={closeSettings}
      ></div>

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-full max-w-sm bg-card border-l border-border z-50 shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${translateX}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border bg-card">
          <div className="flex items-center gap-3">
            <Settings2 className="w-5 h-5 text-text-primary" />
            <h2 className="text-[17px] font-semibold text-text-primary">{language === 'id' ? 'Pengaturan Aplikasi' : 'App Settings'}</h2>
          </div>
          <button
            onClick={closeSettings}
            className="p-2 rounded-lg hover:bg-card-hover text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
          
          {/* Dark Mode Toggle */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              {isDarkMode ? <Moon className="w-5 h-5 text-indigo-500" /> : <Sun className="w-5 h-5 text-amber-500" />}
              <h3 className="font-semibold text-[15px]">{language === 'id' ? 'Tampilan' : 'Appearance'}</h3>
            </div>
            <p className="text-[13px] text-text-muted">{language === 'id' ? 'Beralih antara tema terang dan gelap.' : 'Switch between light and dark themes.'}</p>
            
            <div className="flex items-center justify-between rounded-xl border border-border bg-base p-4">
              <span className="text-[14px] font-medium text-text-primary">{language === 'id' ? 'Mode Gelap' : 'Dark Mode'}</span>
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${isDarkMode ? 'bg-indigo-600' : 'bg-slate-300'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-300 ${isDarkMode ? 'translate-x-6' : ''}`} />
              </button>
            </div>
          </div>

          {/* Language Selector */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              <Languages className="w-5 h-5 text-accent-1" />
              <h3 className="font-semibold text-[15px]">{language === 'id' ? 'Bahasa' : 'Language'}</h3>
            </div>
            <p className="text-[13px] text-text-muted">{language === 'id' ? 'Pilih bahasa antarmuka pilihan Anda.' : 'Choose your preferred interface language.'}</p>
            
            <div className="rounded-xl border border-border bg-base p-1">
              <div className="grid grid-cols-2 gap-1 relative">
                <button
                  onClick={() => setLanguage('en')}
                  className={`py-2 text-[14px] font-medium rounded-lg transition-all z-10 ${
                    language === 'en' ? 'text-text-primary' : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  English
                </button>
                <button
                  onClick={() => setLanguage('id')}
                  className={`py-2 text-[14px] font-medium rounded-lg transition-all z-10 ${
                    language === 'id' ? 'text-text-primary' : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  Bahasa Indonesia
                </button>

                {/* Animated Background Pill */}
                <div 
                  className={`absolute top-0 bottom-0 w-1/2 bg-card rounded-lg shadow-sm border border-border transition-transform duration-300 ease-in-out ${
                    language === 'id' ? 'translate-x-full' : 'translate-x-0'
                  }`}
                ></div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </>
  );
}
