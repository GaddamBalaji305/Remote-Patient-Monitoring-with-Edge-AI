import React, { useRef, useEffect } from 'react';

export default function ECGVisualizer({ dataPoints = [], color = "#10b981", height = 120, label = "ECG Lead II (mV)" }) {
  const canvasRef = useRef(null);
  const dataBufferRef = useRef([]);

  // Accumulate waveform stream into smooth rolling buffer
  useEffect(() => {
    if (dataPoints && dataPoints.length > 0) {
      // Append new incoming array to buffer
      dataBufferRef.current = [...dataBufferRef.current, ...dataPoints].slice(-600); // keep 600 points (~6s)
    }
  }, [dataPoints]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      const width = canvas.width;
      const h = canvas.height;
      
      // Clear canvas
      ctx.clearRect(0, 0, width, h);

      const buffer = dataBufferRef.current;
      if (buffer.length < 2) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      const centerY = h / 2;
      const amplitude = h * 0.35; // Scale height

      // Draw glowing oscilloscope signal trace
      ctx.beginPath();
      ctx.lineWidth = 2.0;
      ctx.strokeStyle = color;
      ctx.shadowBlur = 8;
      ctx.shadowColor = color;
      ctx.lineJoin = "round";

      const step = width / (buffer.length - 1);
      
      for (let i = 0; i < buffer.length; i++) {
        const x = i * step;
        // Invert signal for standard ECG peak orientation
        const y = centerY - (buffer[i] * amplitude);
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Reset shadow for sweep line
      ctx.shadowBlur = 0;

      // Render leading bright point
      const lastX = (buffer.length - 1) * step;
      const lastY = centerY - (buffer[buffer.length - 1] * amplitude);
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3.5, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffffff";
      ctx.fill();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [color]);

  return (
    <div className="oscilloscope-box" style={{ width: '100%', height: `${height}px`, position: 'relative' }}>
      <div style={{ position: 'absolute', top: '6px', left: '10px', fontSize: '0.7rem', color: color, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', zIndex: 2 }}>
        {label}
      </div>
      <canvas
        ref={canvasRef}
        width={500}
        height={height}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
    </div>
  );
}
