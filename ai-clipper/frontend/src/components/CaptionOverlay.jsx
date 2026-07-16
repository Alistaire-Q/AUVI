import React, { useState, useEffect, useMemo } from 'react';
import useClipStore from '../store/useClipStore';

// MILLISECOND MERGING LOGIC
// Extremely fast speech creates subtitle chunks too fast to read.
// If a chunk is < 0.3s and the next chunk is adjacent (gap < 0.2s), we merge them.
const mergeFastSubtitles = (wordsArray) => {
  if (!wordsArray || wordsArray.length === 0) return [];
  
  const merged = [];
  let current = { ...wordsArray[0] };
  
  for (let i = 1; i < wordsArray.length; i++) {
    const nextWord = wordsArray[i];
    const duration = current.end - current.start;
    const gap = nextWord.start - current.end;
    
    if (duration < 0.3 && gap < 0.2) {
      // Merge with next word
      current.word = current.word + " " + nextWord.word;
      current.end = nextWord.end;
    } else {
      merged.push(current);
      current = { ...nextWord };
    }
  }
  merged.push(current);
  
  return merged;
};

export default function CaptionOverlay({ words, currentTime, baseTime = 0 }) {
  const { settings } = useClipStore();
  const [activeWords, setActiveWords] = useState([]);
  
  // Apply Millisecond Merging
  const processedWords = useMemo(() => mergeFastSubtitles(words), [words]);
  
  // Return early if captions are disabled
  if (settings.caption_style === 'none' || !processedWords || processedWords.length === 0) {
    return null;
  }

  // Adjust currentTime by the base time (the start time of the clip within the original video)
  const adjustedTime = baseTime + currentTime;

  useEffect(() => {
    // Find the current active word and surrounding words for context
    let activeIndex = -1;
    
    // Find the word being spoken currently
    for (let i = 0; i < processedWords.length; i++) {
      if (adjustedTime >= processedWords[i].start && adjustedTime <= processedWords[i].end + 0.1) {
        activeIndex = i;
        break;
      }
    }
    
    // If no word is currently active, find the closest upcoming word within 0.5s
    if (activeIndex === -1) {
      for (let i = 0; i < processedWords.length; i++) {
        if (processedWords[i].start > adjustedTime && processedWords[i].start - adjustedTime < 0.5) {
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
    let windowEnd = Math.min(processedWords.length - 1, windowStart + maxWords - 1);
    
    // Adjust window if we're near the end
    if (windowEnd - windowStart + 1 < maxWords && windowStart > 0) {
      windowStart = Math.max(0, windowEnd - maxWords + 1);
    }

    const currentWindow = processedWords.slice(windowStart, windowEnd + 1).map((w, idx) => ({
      ...w,
      isActive: (windowStart + idx) === activeIndex,
      isPast: (windowStart + idx) < activeIndex,
    }));

    // SYNCHRONOUS STATE UPDATE: Bypassing animations forces an instant update.
    setActiveWords(currentWindow);
  }, [adjustedTime, processedWords]);

  if (activeWords.length === 0) return null;

  if (settings.caption_style === 'standard') {
    // Standard subtitles style - constrained to 9:16 video area
    return (
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
        <div className="relative h-full aspect-[9/16] max-w-full">
          <div className="absolute bottom-[8%] left-0 right-0 flex justify-center px-3">
            <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10 shadow-lg inline-block">
              <p className="text-white font-medium text-lg text-center tracking-wide text-shadow-md">
                {activeWords.map(w => w.word).join(' ').toUpperCase()}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Word-by-word viral style — constrained to 9:16 video area
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
      <div className="relative h-full aspect-[9/16] max-w-full">
        <div className="absolute bottom-[8%] left-0 right-0 flex justify-center px-3">
          <div className="flex flex-wrap justify-center gap-x-2 gap-y-1">
            {activeWords.map((wordObj, i) => (
              <span 
                key={`${wordObj.start}-${i}`}
                className={`text-2xl font-black transform ${
                  wordObj.isActive 
                    ? 'text-yellow-300 scale-110 drop-shadow-[0_0_8px_rgba(250,204,21,0.6)]' 
                    : wordObj.isPast 
                      ? 'text-white/90' 
                      : 'text-white/50'
                }`}
                style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.8)' }}
              >
                {wordObj.word.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
