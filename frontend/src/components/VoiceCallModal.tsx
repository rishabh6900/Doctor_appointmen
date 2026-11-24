import { useState, useEffect, useRef } from 'react';
import type { CallState, CallTranscriptMessage } from '../types';
import { AudioWaveform } from './AudioWaveform';
import { api } from '../services/api';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  X,
  AlertCircle,
  Sparkles,
  Bot,
  User as UserIcon,
  Send,
  Loader2,
  Volume2,
} from 'lucide-react';

interface VoiceCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAppointmentUpdated: () => void;
}

// Support for webkitSpeechRecognition
interface IWindow extends Window {
  webkitSpeechRecognition?: any;
  SpeechRecognition?: any;
}

export const VoiceCallModal = ({
  isOpen,
  onClose,
  onAppointmentUpdated,
}: VoiceCallModalProps) => {
  const [callState, setCallState] = useState<CallState>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [typedInput, setTypedInput] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<CallTranscriptMessage[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [fsmState, setFsmState] = useState<string>('LISTENING');

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const isCallActiveRef = useRef(false);
  const speechSafetyTimerRef = useRef<number | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);

  // Deterministically select and lock ONE consistent, pleasant voice for the entire call
  const getOrSelectVoice = (): SpeechSynthesisVoice | null => {
    if (selectedVoiceRef.current) return selectedVoiceRef.current;
    if (!('speechSynthesis' in window)) return null;

    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return null;

    // Preference: Modern natural voices -> Google English -> Pleasant en-US female voices
    const chosen =
      voices.find((v) => v.lang === 'en-US' && (v.name.includes('Natural') || v.name.includes('Online'))) ||
      voices.find((v) => v.name.includes('Google US English') || v.name.includes('Google UK English Female')) ||
      voices.find((v) => v.name.includes('Zira') || v.name.includes('Jenny') || v.name.includes('Samantha') || v.name.includes('Victoria')) ||
      voices.find((v) => v.lang === 'en-US') ||
      voices.find((v) => v.lang.startsWith('en')) ||
      voices[0];

    if (chosen) {
      selectedVoiceRef.current = chosen;
    }
    return chosen;
  };

  // Preload and cache speech synthesis voices on mount
  useEffect(() => {
    if ('speechSynthesis' in window) {
      const initVoices = () => {
        getOrSelectVoice();
      };
      initVoices();
      window.speechSynthesis.onvoiceschanged = initVoices;
    }
  }, []);

  // Auto-scroll transcript
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcripts, interimText]);

  // Duration timer
  useEffect(() => {
    if (callState === 'connected') {
      timerRef.current = window.setInterval(() => {
        setCallDuration((d) => d + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callState]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Speak assistant response aloud using consistent, natural voice parameters
  const speakText = (text: string) => {
    if (!('speechSynthesis' in window)) return;

    if (speechSafetyTimerRef.current) {
      clearTimeout(speechSafetyTimerRef.current);
      speechSafetyTimerRef.current = null;
    }

    // Always unpause synthesis before speaking
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    window.speechSynthesis.cancel();

    // 50ms timeout prevents Chromium from cancelling the new utterance during cancel teardown
    window.setTimeout(() => {
      if (!isCallActiveRef.current) return;
      try {
        const utterance = new SpeechSynthesisUtterance(text);
        utteranceRef.current = utterance;
        
        // Pacing: 0.93 rate + 1.05 pitch sounds human, warm, and natural
        utterance.rate = 0.93;
        utterance.pitch = 1.05;
        utterance.lang = 'en-US';

        const lockedVoice = getOrSelectVoice();
        if (lockedVoice) {
          utterance.voice = lockedVoice;
        }

        const resetSpeaking = () => {
          setIsAssistantSpeaking(false);
          if (speechSafetyTimerRef.current) {
            clearTimeout(speechSafetyTimerRef.current);
            speechSafetyTimerRef.current = null;
          }
        };

        utterance.onstart = () => {
          setIsAssistantSpeaking(true);
          const maxDurationMs = Math.min(15000, Math.max(3000, text.length * 90));
          speechSafetyTimerRef.current = window.setTimeout(resetSpeaking, maxDurationMs);
        };
        utterance.onend = resetSpeaking;
        utterance.onerror = (e) => {
          console.warn('Speech synthesis note:', e);
          resetSpeaking();
        };

        window.speechSynthesis.resume();
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error('Speech synthesis playback error:', err);
        setIsAssistantSpeaking(false);
      }
    }, 50);
  };

  // Handle sending a user utterance (from speech or typed) to backend
  const handleUserMessage = async (userText: string) => {
    const cleanText = userText.trim();
    if (!cleanText || isProcessing) return;

    const userMsg: CallTranscriptMessage = {
      id: Math.random().toString(),
      sender: 'user',
      text: cleanText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };

    setTranscripts((prev) => [...prev, userMsg]);
    setInterimText('');
    setTypedInput('');
    setIsProcessing(true);

    try {
      // Build conversation history
      const history = transcripts.slice(-6).map((t) => ({
        role: t.sender === 'user' ? 'user' : 'model',
        text: t.text,
      }));

      const res = await api.sendVoiceInteract(cleanText, sessionIdRef.current || undefined, history);
      sessionIdRef.current = res.session_id;
      if (res.current_state) {
        setFsmState(res.current_state);
      }

      const aiMsg: CallTranscriptMessage = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: res.response_text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      };

      setTranscripts((prev) => [...prev, aiMsg]);
      speakText(res.response_text);

      if (res.appointment_updated) {
        onAppointmentUpdated();
      }
    } catch (err: any) {
      console.error('Voice interaction error:', err);
      const fallbackMsg: CallTranscriptMessage = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: "I heard you, but had trouble reaching the clinical scheduling engine. Please try once more.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      };
      setTranscripts((prev) => [...prev, fallbackMsg]);
      speakText(fallbackMsg.text);
    } finally {
      setIsProcessing(false);
    }
  };

  // Initialize Speech Recognition
  const initSpeechRecognition = () => {
    const win = window as unknown as IWindow;
    const SpeechRec = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRec) {
      console.warn('Web Speech API is not supported in this browser.');
      return null;
    }

    const recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      if (isMuted || isAssistantSpeaking) return;

      let interim = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcriptPart = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPart;
        } else {
          interim += transcriptPart;
        }
      }

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      if (interim) {
        setInterimText(interim);
        // Silence debounce: dispatch if caller stops speaking and browser delays isFinal
        silenceTimerRef.current = window.setTimeout(() => {
          if (interim.trim() && !isProcessing) {
            handleUserMessage(interim);
          }
        }, 1200);
      }

      if (finalTranscript.trim()) {
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
        handleUserMessage(finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      // Ignore routine 'no-speech' or 'aborted'
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.warn('Speech recognition status:', event.error);
      }
    };

    recognition.onend = () => {
      // Auto-restart while call is active
      if (isCallActiveRef.current && !isMuted) {
        try {
          recognition.start();
        } catch {
          // already started or busy
        }
      }
    };

    return recognition;
  };

  const startCall = async () => {
    setErrorMessage(null);
    setTranscripts([]);
    setCallDuration(0);
    setCallState('requesting_mic');
    isCallActiveRef.current = true;

    try {
      // 1. Audio stream capture for visualizer & WebRTC
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });
      localStreamRef.current = stream;

      // 2. Set up Web Audio Analyser for dynamic waveform
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      setCallState('connecting');

      // 3. Start Browser Speech Recognition for instant speech-to-text
      const rec = initSpeechRecognition();
      if (rec) {
        recognitionRef.current = rec;
        try {
          rec.start();
        } catch (e) {
          console.warn('Recognition start note:', e);
        }
      }

      // 4. Background WebRTC Signaling (optional real-time channel)
      try {
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        });
        pcRef.current = pc;

        // Route incoming remote audio track from Pipecat to browser speaker
        pc.ontrack = (event) => {
          console.log('[WebRTC] Received remote audio track from Pipecat:', event.track);
          if (remoteAudioRef.current) {
            remoteAudioRef.current.srcObject = event.streams[0] || new MediaStream([event.track]);
            remoteAudioRef.current.play().catch((err) => console.warn('Remote audio autoplay note:', err));
          }
        };

        stream.getTracks().forEach((track) => pc.addTrack(track, stream));

        const offer = await pc.createOffer({ offerToReceiveAudio: true });
        await pc.setLocalDescription(offer);

        // Await ICE completion
        if (pc.iceGatheringState !== 'complete') {
          await new Promise<void>((resolve) => {
            const check = () => {
              if (pc.iceGatheringState === 'complete') {
                pc.removeEventListener('icegatheringstatechange', check);
                resolve();
              }
            };
            pc.addEventListener('icegatheringstatechange', check);
            setTimeout(() => {
              pc.removeEventListener('icegatheringstatechange', check);
              resolve();
            }, 800);
          });
        }

        const sdpToSend = pc.localDescription?.sdp || offer.sdp || '';
        const response = await api.sendVoiceOffer(sdpToSend, offer.type);
        sessionIdRef.current = response.session_id;

        if (pcRef.current && pc.signalingState !== 'closed') {
          await pc.setRemoteDescription({
            type: response.type as RTCSdpType,
            sdp: response.sdp,
          });
        }
      } catch (webrtcErr) {
        console.info('WebRTC peer note (Web Speech active):', webrtcErr);
      }

      setCallState('connected');

      // 5. Welcome Greeting
      const welcomeText = "Hello! Thank you for calling CarePoint Health Medical Clinic. I'm your AI appointment assistant. How may I help you today?";
      setTranscripts([
        {
          id: 'welcome',
          sender: 'assistant',
          text: welcomeText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        },
      ]);

      // Ensure the voice lock is loaded so greeting uses the exact same voice as subsequent turns
      const voice = getOrSelectVoice();
      if (voice) {
        speakText(welcomeText);
      } else {
        setTimeout(() => {
          getOrSelectVoice();
          speakText(welcomeText);
        }, 120);
      }

    } catch (err: unknown) {
      console.error('Call establishment error:', err);
      const msg = err instanceof Error ? err.message : 'Failed to access microphone or initialize audio.';
      setErrorMessage(msg);
      setCallState('failed');
      cleanupMedia();
    }
  };

  const cleanupMedia = () => {
    isCallActiveRef.current = false;
    setIsAssistantSpeaking(false);
    if (speechSafetyTimerRef.current) {
      clearTimeout(speechSafetyTimerRef.current);
      speechSafetyTimerRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // already stopped
      }
      recognitionRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop());
      localStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    analyserRef.current = null;
    setIsAssistantSpeaking(false);
    setIsProcessing(false);
    setInterimText('');
  };

  const endCall = async () => {
    setCallState('ended');
    if (sessionIdRef.current) {
      try {
        await api.endVoiceSession(sessionIdRef.current);
      } catch (e) {
        console.warn('Session end notification:', e);
      }
      sessionIdRef.current = null;
    }
    cleanupMedia();
    onAppointmentUpdated();
  };

  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        const newMuted = !audioTrack.enabled;
        setIsMuted(newMuted);

        if (newMuted && recognitionRef.current) {
          try {
            recognitionRef.current.stop();
          } catch {}
        } else if (!newMuted && recognitionRef.current && isCallActiveRef.current) {
          try {
            recognitionRef.current.start();
          } catch {}
        }
      }
    }
  };

  const handleClose = () => {
    if (callState === 'connected' || callState === 'ringing' || callState === 'connecting') {
      endCall();
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[92vh] border border-slate-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-teal-700 to-navy-900 px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-teal-200" />
            </div>
            <div>
              <h3 className="font-semibold text-base">CarePoint AI Receptionist</h3>
              <p className="text-xs text-teal-200 flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    callState === 'connected'
                      ? 'bg-emerald-400 animate-pulse'
                      : callState === 'failed'
                      ? 'bg-rose-400'
                      : 'bg-amber-300'
                  }`}
                ></span>
                <span className="capitalize">{callState}</span>
                {callState === 'connected' && ` • ${formatDuration(callDuration)}`}
                {callState === 'connected' && fsmState && fsmState !== 'LISTENING' && (
                  <span className="bg-teal-800/80 text-teal-100 text-[10px] px-2 py-0.5 rounded-full font-medium ml-1 capitalize">
                    {fsmState.replace(/_/g, ' ').toLowerCase()}
                  </span>
                )}
                {isAssistantSpeaking && (
                  <span className="flex items-center gap-1 text-emerald-300 ml-1">
                    <Volume2 className="w-3.5 h-3.5 animate-pulse" /> Speaking
                  </span>
                )}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-white/70 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 flex-1 flex flex-col space-y-4 overflow-hidden">
          {/* Hidden Remote Audio Output element for WebRTC audio tracks */}
          <audio ref={remoteAudioRef} autoPlay playsInline className="hidden" />

          {/* Waveform Visualization */}
          <AudioWaveform
            analyser={analyserRef.current}
            isActive={callState === 'connected' && (!isMuted || isAssistantSpeaking)}
          />

          {/* Error Banner */}
          {errorMessage && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-start gap-2 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Voice Connection Note</p>
                <p className="mt-0.5">{errorMessage}</p>
              </div>
            </div>
          )}

          {/* Transcript Scroll Area */}
          <div className="flex-1 min-h-[220px] bg-slate-50 rounded-2xl p-4 overflow-y-auto space-y-3 border border-slate-200" ref={scrollRef}>
            {transcripts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-8">
                <Sparkles className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium">Spoken conversation transcript will stream here.</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Try saying: "I want to check Dr. Sarah Jenkins availability tomorrow"
                </p>
              </div>
            ) : (
              transcripts.map((t) => (
                <div
                  key={t.id}
                  className={`flex gap-2.5 ${t.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {t.sender !== 'user' && (
                    <div className="w-7 h-7 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center shrink-0 text-xs font-bold">
                      AI
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                      t.sender === 'user'
                        ? 'bg-teal-600 text-white rounded-br-none shadow-sm'
                        : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{t.text}</p>
                    <span
                      className={`block text-[10px] mt-1 ${
                        t.sender === 'user' ? 'text-teal-200 text-right' : 'text-slate-400'
                      }`}
                    >
                      {t.timestamp}
                    </span>
                  </div>
                  {t.sender === 'user' && (
                    <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0">
                      <UserIcon className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              ))
            )}

            {/* Interim live speech recognition display */}
            {interimText && (
              <div className="flex justify-end gap-2.5 animate-pulse">
                <div className="max-w-[80%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed bg-teal-500/80 text-white rounded-br-none shadow-sm italic">
                  <p>{interimText}...</p>
                </div>
                <div className="w-7 h-7 rounded-full bg-teal-200 text-teal-800 flex items-center justify-center shrink-0 text-xs">
                  <Mic className="w-3.5 h-3.5 animate-bounce" />
                </div>
              </div>
            )}

            {/* Processing indicator */}
            {isProcessing && (
              <div className="flex justify-start gap-2.5">
                <div className="w-7 h-7 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center shrink-0 text-xs font-bold">
                  AI
                </div>
                <div className="rounded-2xl px-3.5 py-2 text-xs bg-white text-slate-500 border border-slate-200 rounded-bl-none shadow-sm flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600" />
                  <span>Checking clinical records & schedules...</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Voice/Text Interactive Bar (Visible during call) */}
          {callState === 'connected' && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleUserMessage(typedInput);
              }}
              className="flex items-center gap-2 pt-1"
            >
              <input
                type="text"
                placeholder={isMuted ? "Mic is muted. Type your message here..." : "Speak into your mic, or type message here..."}
                value={typedInput}
                onChange={(e) => setTypedInput(e.target.value)}
                disabled={isProcessing}
                className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
              />
              <button
                type="submit"
                disabled={!typedInput.trim() || isProcessing}
                className="p-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white rounded-xl transition-colors shadow-sm"
                title="Send message"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </div>

        {/* Call Controls Footer */}
        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex items-center justify-center gap-4">
          {callState === 'idle' || callState === 'ended' || callState === 'failed' ? (
            <button
              onClick={startCall}
              className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm px-6 py-3 rounded-2xl shadow-md hover:shadow-lg transition-all"
            >
              <Phone className="w-4 h-4" />
              <span>Start Voice Consultation</span>
            </button>
          ) : (
            <>
              <button
                onClick={toggleMute}
                className={`p-3.5 rounded-2xl font-medium text-xs transition-colors ${
                  isMuted
                    ? 'bg-amber-100 text-amber-900 border border-amber-300'
                    : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                }`}
                title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
              >
                {isMuted ? <MicOff className="w-5 h-5 text-amber-700" /> : <Mic className="w-5 h-5 text-slate-600" />}
              </button>

              <button
                onClick={endCall}
                className="inline-flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-sm px-6 py-3 rounded-2xl shadow-md hover:shadow-lg transition-all"
              >
                <PhoneOff className="w-4 h-4" />
                <span>End Call</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
