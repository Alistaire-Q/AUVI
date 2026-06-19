import React, { useEffect, useState } from 'react';
import { X, Settings2, SlidersHorizontal, Languages, Type, Clock } from 'lucide-react';
import useClipStore from '../store/useClipStore';

export default function SettingsDrawer() {
  const { settingsOpen, closeSettings, settings, updateSettings, resetSettings } = useClipStore();
  const [localSettings, setLocalSettings] = useState(settings);

  // Sync local state when global settings change
  useEffect(() => {
    setLocalSettings(settings);
  }, [settings, settingsOpen]);

  // If closed, translate it off screen
  const translateX = settingsOpen ? 'translate-x-0' : 'translate-x-full';
  
  const handleSave = () => {
    updateSettings(localSettings);
    closeSettings();
  };

  const handleChange = (key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
  };

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
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-surface border-l border-border z-50 shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${translateX}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <Settings2 className="w-6 h-6 text-accent-1" />
            <h2 className="text-xl font-bold text-text-primary">Processing Settings</h2>
          </div>
          <button 
            onClick={closeSettings}
            className="p-2 rounded-full hover:bg-border text-text-muted hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
          
          {/* Clip Duration */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              <Clock className="w-5 h-5 text-accent-2" />
              <h3 className="font-semibold">Target Clip Duration</h3>
            </div>
            <p className="text-sm text-text-muted">How long should each generated clip be?</p>
            
            <div className="grid grid-cols-3 gap-3">
              {[15, 30, 60].map(duration => (
                <button
                  key={duration}
                  className={`py-2 px-4 rounded-lg border text-sm font-medium transition-all ${
                    localSettings.clip_duration === duration
                      ? 'border-accent-1 bg-accent-1/10 text-accent-1'
                      : 'border-border bg-card text-text-muted hover:border-text-muted'
                  }`}
                  onClick={() => handleChange('clip_duration', duration)}
                >
                  {duration}s
                </button>
              ))}
            </div>
            {/* Custom duration input could be added here, omitting for simplicity of layout */}
          </div>

          {/* Max Clips */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              <ScissorsIcon className="w-5 h-5 text-accent-2" />
              <h3 className="font-semibold">Maximum Clips</h3>
            </div>
            <p className="text-sm text-text-muted">Maximum number of clips to generate per video.</p>
            
            <div className="grid grid-cols-4 gap-3">
              {[3, 5, 10, 15].map(max => (
                <button
                  key={max}
                  className={`py-2 rounded-lg border text-sm font-medium transition-all ${
                    localSettings.max_clips === max
                      ? 'border-accent-1 bg-accent-1/10 text-accent-1'
                      : 'border-border bg-card text-text-muted hover:border-text-muted'
                  }`}
                  onClick={() => handleChange('max_clips', max)}
                >
                  {max}
                </button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              <Languages className="w-5 h-5 text-accent-2" />
              <h3 className="font-semibold">Transcription Language</h3>
            </div>
            <p className="text-sm text-text-muted">Helps Whisper AI transcribe more accurately.</p>
            
            <select 
              value={localSettings.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="w-full bg-card border border-border rounded-lg p-3 text-text-primary outline-none focus:border-accent-1 transition-colors appearance-none"
            >
              <option value="auto">Auto-Detect</option>
              <option value="en">English</option>
              <option value="id">Indonesian</option>
            </select>
          </div>

          {/* Caption Style */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-primary">
              <Type className="w-5 h-5 text-accent-2" />
              <h3 className="font-semibold">Preview Caption Style</h3>
            </div>
            <p className="text-sm text-text-muted">How captions appear in the preview player.</p>
            
            <div className="flex flex-col gap-2">
              {[
                { id: 'word', label: 'Word-by-Word (Viral)', desc: 'Highlight active words dynamically' },
                { id: 'standard', label: 'Standard Subtitles', desc: 'Show full sentences at once' },
                { id: 'none', label: 'None', desc: 'Disable caption overlay' },
              ].map(style => (
                <button
                  key={style.id}
                  className={`p-3 rounded-lg border text-left transition-all flex flex-col gap-1 ${
                    localSettings.caption_style === style.id
                      ? 'border-accent-1 bg-accent-1/5'
                      : 'border-border bg-card hover:border-text-muted/50'
                  }`}
                  onClick={() => handleChange('caption_style', style.id)}
                >
                  <span className={`font-medium ${localSettings.caption_style === style.id ? 'text-accent-1' : 'text-text-primary'}`}>
                    {style.label}
                  </span>
                  <span className="text-xs text-text-muted">{style.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Min Viral Score */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-text-primary">
                <SlidersHorizontal className="w-5 h-5 text-accent-2" />
                <h3 className="font-semibold">Minimum Viral Score</h3>
              </div>
              <span className="font-bold text-accent-1">{localSettings.min_score}%</span>
            </div>
            <p className="text-sm text-text-muted">Only generate clips that score above this threshold.</p>
            
            <input 
              type="range" 
              min="0" 
              max="100" 
              step="5"
              value={localSettings.min_score}
              onChange={(e) => handleChange('min_score', parseInt(e.target.value))}
              className="w-full h-2 bg-card rounded-lg appearance-none cursor-pointer border border-border accent-accent-1"
            />
            <div className="flex justify-between text-xs text-text-hint mt-1">
              <span>More Clips (Lower Quality)</span>
              <span>Fewer Clips (High Quality)</span>
            </div>
          </div>

        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-border bg-card flex items-center gap-4 mt-auto">
          <button 
            onClick={() => {
              resetSettings();
              setLocalSettings(settings); // Reset local to default too
            }}
            className="px-4 py-2 text-sm font-medium text-text-muted hover:text-white transition-colors"
          >
            Reset
          </button>
          <button 
            onClick={handleSave}
            className="flex-1 btn-primary"
          >
            Save Settings
          </button>
        </div>
      </div>
    </>
  );
}

// Just for icon missing from lucide-react import above
function ScissorsIcon(props) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      {...props}
    >
      <circle cx="6" cy="6" r="3"></circle>
      <circle cx="6" cy="18" r="3"></circle>
      <line x1="20" y1="4" x2="8.12" y2="15.88"></line>
      <line x1="14.47" y1="14.48" x2="20" y2="20"></line>
      <line x1="8.12" y1="8.12" x2="12" y2="12"></line>
    </svg>
  );
}
