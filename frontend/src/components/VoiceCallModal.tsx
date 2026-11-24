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
} from 'lucide-react';

interface VoiceCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAppointmentUpdated: () => void;
}

export const VoiceCallModal = ({
  isOpen,
  onClose,
  onAppointmentUpdated,
}: VoiceCallModalProps) => {
  const [callState, setCallState] = useState<CallState>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<CallTranscriptMessage[]>([]);
  const [callDuration, setCallDuration] = useState(0);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll transcript
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcripts]);

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

  const startCall = async () => {
    setErrorMessage(null);
    setTranscripts([]);
    setCallDuration(0);
    setCallState('requesting_mic');

    try {
      // 1. Audio stream capture
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });
      localStreamRef.current = stream;

      // 2. Set up Web Audio Analyser
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      setCallState('connecting');

      // 3. RTCPeerConnection configuration
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pcRef.current = pc;

      // Add local audio tracks
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      // Create audio element for remote stream (Pipecat ElevenLabs TTS output)
      const remoteAudio = new Audio();
      remoteAudio.autoplay = true;

      pc.ontrack = (event) => {
        if (event.streams && event.streams[0]) {
          remoteAudio.srcObject = event.streams[0];
          remoteAudio.play().catch(console.error);
        }
      };

      // Optional data channel for real-time transcript/events
      const dc = pc.createDataChannel('pipecat-events');
      dc.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'transcript') {
            setTranscripts((prev) => [
              ...prev,
              {
                id: Math.random().toString(),
                sender: data.sender || 'assistant',
                text: data.text,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
              },
            ]);
            if (data.appointment_changed) {
              onAppointmentUpdated();
            }
          }
        } catch {
          // Plain text message
          setTranscripts((prev) => [
            ...prev,
            {
              id: Math.random().toString(),
              sender: 'assistant',
              text: event.data,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            },
          ]);
        }
      };

      // Create offer
      const offer = await pc.createOffer({
        offerToReceiveAudio: true,
      });
      await pc.setLocalDescription(offer);

      setCallState('ringing');

      // Send offer to FastAPI backend
      const response = await api.sendVoiceOffer(offer.sdp || '', offer.type);
      sessionIdRef.current = response.session_id;

      // Set backend answer
      await pc.setRemoteDescription({
        type: response.type as RTCSdpType,
        sdp: response.sdp,
      });

      setCallState('connected');
      setTranscripts([
        {
          id: 'welcome',
          sender: 'assistant',
          text: "Hello! Thank you for calling CarePoint Health Medical Clinic. I'm your AI appointment assistant. How may I help you today?",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        },
      ]);
    } catch (err: unknown) {
      console.error('Call establishment error:', err);
      const msg = err instanceof Error ? err.message : 'Failed to establish WebRTC connection.';
      setErrorMessage(msg);
      setCallState('failed');
      cleanupMedia();
    }
  };

  const cleanupMedia = () => {
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
        setIsMuted(!audioTrack.enabled);
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
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh] border border-slate-200">
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
        <div className="p-6 flex-1 flex flex-col space-y-5 overflow-hidden">
          {/* Waveform Visualization */}
          <AudioWaveform
            analyser={analyserRef.current}
            isActive={callState === 'connected' && !isMuted}
          />

          {/* Error Banner */}
          {errorMessage && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-start gap-2 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Voice Connection Note</p>
                <p className="mt-0.5">{errorMessage}</p>
                <p className="text-slate-500 mt-1">
                  Ensure backend is running on port 8000 and valid AI API keys are configured.
                </p>
              </div>
            </div>
          )}

          {/* Transcript Scroll Area */}
          <div className="flex-1 min-h-[180px] bg-slate-50 rounded-2xl p-4 overflow-y-auto space-y-3 border border-slate-200" ref={scrollRef}>
            {transcripts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-8">
                <Sparkles className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium">Spoken conversation transcript will stream here.</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Try asking: "I want an appointment with Dr. Sarah Jenkins tomorrow at 10 AM"
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
                    className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                      t.sender === 'user'
                        ? 'bg-teal-600 text-white rounded-br-none shadow-sm'
                        : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                    }`}
                  >
                    <p>{t.text}</p>
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
          </div>
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
