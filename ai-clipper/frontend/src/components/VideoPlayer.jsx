import React, { useRef, useState, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';

const VideoPlayer = forwardRef(({ src, poster, onTimeUpdate, autoPlay = false, defaultDuration = 0, children }, ref) => {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const isSeeking = useRef(false);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(defaultDuration || 0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (defaultDuration > 0 && (!duration || duration === 0 || isNaN(duration) || duration === Infinity)) {
      setDuration(defaultDuration);
    }
  }, [defaultDuration]);

  useImperativeHandle(ref, () => ({
    seekTo: (time) => {
      if (videoRef.current) {
        videoRef.current.currentTime = time;
        setCurrentTime(time);
      }
    },
    getCurrentTime: () => videoRef.current?.currentTime || 0,
    getDuration: () => videoRef.current?.duration || duration || defaultDuration || 0,
    play: () => videoRef.current?.play(),
    pause: () => videoRef.current?.pause(),
  }));

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateDuration = () => {
      if (video.duration && !isNaN(video.duration) && video.duration !== Infinity) {
        setDuration(video.duration);
      } else if (defaultDuration > 0 && (!duration || duration === 0)) {
        setDuration(defaultDuration);
      }
    };

    updateDuration();

    const handleTimeUpdate = () => {
      if (isSeeking.current) return;
      setCurrentTime(video.currentTime);
      if (onTimeUpdate) onTimeUpdate(video.currentTime);
      if (!duration || duration === 0 || isNaN(duration) || duration === Infinity) {
        updateDuration();
      }
    };

    const handleDurationChange = () => updateDuration();
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    
    const handleSeeked = () => {
      if (!isSeeking.current) {
        setCurrentTime(video.currentTime);
        if (onTimeUpdate) onTimeUpdate(video.currentTime);
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('loadedmetadata', updateDuration);
    video.addEventListener('loadeddata', updateDuration);
    video.addEventListener('canplay', updateDuration);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('seeked', handleSeeked);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('loadedmetadata', updateDuration);
      video.removeEventListener('loadeddata', updateDuration);
      video.removeEventListener('canplay', updateDuration);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('seeked', handleSeeked);
    };
  }, [onTimeUpdate, defaultDuration, duration]);

  useEffect(() => {
    if (autoPlay && videoRef.current) {
      videoRef.current.play().catch(e => console.log('Auto-play prevented:', e));
    }
  }, [autoPlay, src]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) videoRef.current.pause();
      else videoRef.current.play();
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      if (val > 0 && isMuted) {
        setIsMuted(false);
        videoRef.current.muted = false;
      }
    }
  };

  // Called while user is actively dragging/interacting with the slider
  const handleSeekInput = useCallback((e) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    // Update video position in real-time for visual feedback
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  }, []);

  // Mark the start of a seek interaction (mouse/touch down on slider)
  const handleSeekStart = useCallback(() => {
    isSeeking.current = true;
  }, []);

  // Mark the end of a seek interaction and commit the final position
  const handleSeekEnd = useCallback((e) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
    setCurrentTime(time);
    if (onTimeUpdate) onTimeUpdate(time);
    isSeeking.current = false;
  }, [onTimeUpdate]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const formatTime = (timeInSeconds) => {
    if (!timeInSeconds || isNaN(timeInSeconds) || timeInSeconds === Infinity) return '0:00';
    const m = Math.floor(timeInSeconds / 60);
    const s = Math.floor(timeInSeconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      ref={containerRef} 
      className="relative w-full bg-black rounded-xl overflow-hidden group border border-border"
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full h-full aspect-video object-contain cursor-pointer"
        onClick={togglePlay}
      />
      
      {/* Overlay children (e.g. CaptionOverlay) */}
      {children}

      {/* Controls Overlay */}
      <div className="absolute bottom-0 left-0 right-0 player-controls opacity-0 group-hover:opacity-100 transition-opacity flex-col items-stretch pt-8">
        <div className="flex items-center gap-2 mb-2 w-full">
          <input
            type="range"
            min={0}
            max={duration || defaultDuration || 100}
            value={currentTime}
            onMouseDown={handleSeekStart}
            onTouchStart={handleSeekStart}
            onInput={handleSeekInput}
            onChange={handleSeekEnd}
            className="w-full"
            step="0.1"
          />
        </div>
        
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4">
            <button onClick={togglePlay} className="text-white hover:text-accent-1 transition-colors">
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            
            <div className="flex items-center gap-2 group/volume">
              <button onClick={toggleMute} className="text-white hover:text-accent-1 transition-colors">
                {isMuted || volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-20 opacity-0 group-hover/volume:opacity-100 transition-opacity"
              />
            </div>
            
            <span className="text-white text-xs font-medium">
              {formatTime(currentTime)} / {formatTime(duration || defaultDuration || 0)}
            </span>
          </div>
          
          <button onClick={toggleFullscreen} className="text-white hover:text-accent-1 transition-colors">
            <Maximize className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
});

export default VideoPlayer;
