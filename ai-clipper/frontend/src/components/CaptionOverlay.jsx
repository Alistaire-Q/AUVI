import React, { useState, useEffect } from 'react';
import useClipStore from '../store/useClipStore';

export default function CaptionOverlay({ words, currentTime, baseTime = 0 }) {
  const { settings } = useClipStore();
  const [activeWords, setActiveWords] = useState([]);
  
  // Return early if captions are disabled
  if (settings.caption_style === 'none' || !words || words.length === 0) {
    return null;
  }

  // Adjust currentTime by the base time (the start time of the clip within the original video)
  const adjustedTime = baseTime + currentTime;

  useEffect(() => {
    // Find the current active word and surrounding words for context
    let activeIndex = -1;
    
    // Find the word being spoken currently
    for (let i = 0; i < words.length; i++) {
      if (adjustedTime >= words[i].start && adjustedTime <= words[i].end + 0.1) {
        activeIndex = i;
        break;
      }
    }
    
    // If no word is currently active, find the closest upcoming word within 0.5s
    if (activeIndex === -1) {
      for (let i = 0; i < words.length; i++) {
        if (words[i].start > adjustedTime && words[i].start - adjustedTime < 0.5) {
          activeIndex = i;
          break;
        }
      }
    }

    if (activeIndex === -1) {
      setActiveWords([]);
      return;
    }

    // Determine the window of words to show (max 6-8 words per screen)
    // Try to break at logical boundaries or keep the active word centered
    const maxWords = 8;
    let windowStart = Math.max(0, activeIndex - 3);
    let windowEnd = Math.min(words.length - 1, windowStart + maxWords - 1);
    
    // Adjust window if we're near the end
    if (windowEnd - windowStart + 1 < maxWords && windowStart > 0) {
      windowStart = Math.max(0, windowEnd - maxWords + 1);
    }

    const currentWindow = words.slice(windowStart, windowEnd + 1).map((w, idx) => ({
      ...w,
      isActive: (windowStart + idx) === activeIndex,
      isPast: (windowStart + idx) < activeIndex,
    }));

    setActiveWords(currentWindow);
  }, [adjustedTime, words]);

  if (activeWords.length === 0) return null;

  if (settings.caption_style === 'standard') {
    // Standard subtitles style - just show the text without word-by-word highlights
    return (
      <div className="caption-container">
        <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10 shadow-lg inline-block">
          <p className="text-white font-medium text-lg text-center tracking-wide text-shadow-md">
            {activeWords.map(w => w.word).join(' ')}
          </p>
        </div>
      </div>
    );
  }

  // Word-by-word viral style
  return (
    <div className="caption-container w-full px-8 flex justify-center">
      <div className="flex flex-wrap justify-center gap-x-2 gap-y-1">
        {activeWords.map((wordObj, i) => (
          <span 
            key={`${wordObj.start}-${i}`}
            className={`caption-word transform transition-all duration-150 ${
              wordObj.isActive 
                ? 'active scale-110' 
                : wordObj.isPast 
                  ? 'text-white' 
                  : 'text-white/60'
            }`}
          >
            {wordObj.word}
          </span>
        ))}
      </div>
    </div>
  );
}
