import React from 'react';
import { X, Heart, Activity, Thermometer, Wind, ShieldAlert, Cpu, CheckCircle, FileText } from 'lucide-react';
import ECGVisualizer from './ECGVisualizer';

export default function PatientDetailModal({ patient, telemetry, onClose }) {
  if (!patient) return null;

  const vitals = telemetry?.vitals || {
    heart_rate: patient.baseline_hr,
    spo2: patient.baseline_spo2,
    sys_bp: patient.baseline_sys_bp,
    dia_bp: patient.baseline_dia_bp,
    temperature: patient.baseline_temp,
    respiratory_rate: patient.baseline_rr
  };

  const hrv = telemetry?.hrv || {
    mean_rr_ms: 812.5,
    sdnn_ms: 38.2,
    rmssd_ms: 29.4,
    calculated_hr: patient.baseline_hr
  };

  const edgeAnalysis = telemetry?.edge_analysis || {
    is_anomaly: false,
    anomaly_score: 0.05,
    alert_level: "Normal",
    condition: "Normal Sinus Rhythm",
    inference_latency_ms: 4.2
  };

  const ecgWaveform = telemetry?.waveforms?.ecg || [];
  const ppgWaveform = telemetry?.waveforms?.ppg || [];

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      
      <div className="glass-panel" style={{ width: '100%', maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto', padding: '28px', borderRadius: '16px', background: '#0b0f19', border: '1px solid var(--border-highlight)' }}>
        
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>{patient.name}</h2>
              <span className={`badge ${edgeAnalysis.alert_level === "Critical" ? "badge-critical" : edgeAnalysis.alert_level === "Warning" ? "badge-warning" : "badge-normal"}`}>
                {edgeAnalysis.condition}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              ID: {patient.id} • Room: {patient.room} • Gender: {patient.gender}, Age: {patient.age} • Node: {patient.edge_node_id}
            </p>
          </div>

          <button 
            onClick={onClose}
            style={{ background: 'rgba(255,255,255,0.1)', border: 0, color: '#fff', padding: '8px', borderRadius: '50%', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Oscilloscopes Section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} color="var(--accent-cyan)" /> LIVE EDGE WAVEFORM TELEMETRY (100Hz)
          </h3>
          
          <ECGVisualizer 
            dataPoints={ecgWaveform} 
            color={edgeAnalysis.alert_level === "Critical" ? "#ef4444" : "#10b981"} 
            height={130} 
            label="ECG Lead II (mV)" 
          />

          <ECGVisualizer 
            dataPoints={ppgWaveform} 
            color="#06b6d4" 
            height={90} 
            label="PPG Optical Pulse Signal" 
          />
        </div>

        {/* Detailed Metrics & HRV Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          
          {/* Heart Rate & HRV Panel */}
          <div style={{ background: 'rgba(17, 24, 39, 0.8)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-rose)', fontWeight: 600, marginBottom: '8px' }}>
              HEART RATE & HRV ANALYSIS
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span className="mono-val" style={{ fontSize: '2rem', color: '#fff' }}>{Math.round(vitals.heart_rate)}</span>
              <span style={{ color: 'var(--text-muted)' }}>BPM</span>
            </div>
            <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>Mean RR Interval: <strong style={{ color: '#fff' }}>{hrv.mean_rr_ms} ms</strong></div>
              <div>SDNN (Variability): <strong style={{ color: '#fff' }}>{hrv.sdnn_ms} ms</strong></div>
              <div>RMSSD (Vagal Tone): <strong style={{ color: '#fff' }}>{hrv.rmssd_ms} ms</strong></div>
            </div>
          </div>

          {/* Oxygen & Respiration */}
          <div style={{ background: 'rgba(17, 24, 39, 0.8)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '8px' }}>
              OXYGEN & RESPIRATION
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span className="mono-val" style={{ fontSize: '2rem', color: '#fff' }}>{Math.round(vitals.spo2)}%</span>
              <span style={{ color: 'var(--text-muted)' }}>SpO2</span>
            </div>
            <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>Respiratory Rate: <strong style={{ color: '#fff' }}>{vitals.respiratory_rate} breaths/min</strong></div>
              <div>Body Temp: <strong style={{ color: '#fff' }}>{vitals.temperature} °C</strong></div>
              <div>Perfusion Index: <strong style={{ color: '#fff' }}>4.8% (Normal)</strong></div>
            </div>
          </div>

          {/* Edge AI Diagnostic Score */}
          <div style={{ background: 'rgba(17, 24, 39, 0.8)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-indigo)', fontWeight: 600, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={14} /> EDGE AI CLASSIFIER
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span className="mono-val" style={{ fontSize: '2rem', color: edgeAnalysis.anomaly_score > 0.5 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                {(edgeAnalysis.anomaly_score * 100).toFixed(0)}%
              </span>
              <span style={{ color: 'var(--text-muted)' }}>Risk Index</span>
            </div>
            <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>Inference Latency: <strong style={{ color: '#fff' }}>{edgeAnalysis.inference_latency_ms || 4.2} ms</strong></div>
              <div>Model: <strong style={{ color: '#fff' }}>IsolationForest + Pan-Tompkins</strong></div>
              <div>Status: <strong style={{ color: edgeAnalysis.is_anomaly ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>{edgeAnalysis.is_anomaly ? "Anomaly Flagged" : "Normal Sinus"}</strong></div>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button 
            onClick={onClose}
            style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'transparent', color: '#fff', fontWeight: 600, cursor: 'pointer' }}
          >
            Close Diagnostics
          </button>
        </div>

      </div>

    </div>
  );
}
