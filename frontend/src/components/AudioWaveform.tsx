import React, { useEffect, useRef } from 'react';

interface AudioWaveformProps {
  analyser: AnalyserNode | null;
  isActive: boolean;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ analyser, isActive }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const bufferLength = analyser ? analyser.frequencyBinCount : 32;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      animationFrameId = requestAnimationFrame(render);
      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);

      if (!isActive || !analyser) {
        // Render subtle pulsing idle wave
        ctx.beginPath();
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 2;
        const time = Date.now() / 300;
        for (let x = 0; x < width; x++) {
          const y = height / 2 + Math.sin(x * 0.05 + time) * 3;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        return;
      }

      analyser.getByteFrequencyData(dataArray);

      // Render sleek visualizer bars / curve
      const barCount = 36;
      const step = Math.floor(bufferLength / barCount);
      const barWidth = (width / barCount) - 3;

      for (let i = 0; i < barCount; i++) {
        const val = dataArray[i * step] || 0;
        const percent = val / 255;
        const barHeight = Math.max(4, percent * (height - 10));
        const x = i * (barWidth + 3);
        const y = (height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, '#0d9488');
        gradient.addColorStop(1, '#14b8a6');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 3);
        ctx.fill();
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [analyser, isActive]);

  return (
    <div className="w-full bg-slate-900 rounded-2xl p-4 flex flex-col items-center justify-center shadow-inner">
      <canvas
        ref={canvasRef}
        width={360}
        height={72}
        className="w-full max-w-sm h-18"
      />
    </div>
  );
};
