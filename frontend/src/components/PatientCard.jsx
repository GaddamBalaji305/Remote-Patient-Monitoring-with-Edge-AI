import React from 'react';
import { Heart, Activity, Thermometer, Wind, AlertTriangle, Cpu, ChevronRight } from 'lucide-react';
import ECGVisualizer from './ECGVisualizer';

export default function PatientCard({ patient, telemetry, onSelectPatient, activeAnomaly }) {
  const vitals = telemetry?.vitals || {
    heart_rate: patient.baseline_hr,
    spo2: patient.baseline_spo2,
    sys_bp: patient.baseline_sys_bp,
    dia_bp: patient.baseline_dia_bp,
    temperature: patient.baseline_temp,
    respiratory_rate: patient.baseline_rr
  };

  const edgeAnalysis = telemetry?.edge_analysis || {
    is_anomaly: false,
    alert_level: patient.status || "Normal",
    condition: "Normal Sinus Rhythm",
    anomaly_score: 0.05
  };

  const ecgWaveform = telemetry?.waveforms?.ecg || [];

  // Color mappings
  const alertLevel = edgeAnalysis.alert_level;
  const badgeClass = alertLevel === "Critical" ? "badge-critical" : alertLevel === "Warning" ? "badge-warning" : "badge-normal";
  const ecgColor = alertLevel === "Critical" ? "#ef4444" : alertLevel === "Warning" ? "#f59e0b" : "#10b981";

  return (
    <div 
      className="glass-panel" 
      style={{ 
        padding: '20px', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '16px',
        borderLeft: alertLevel === "Critical" ? '4px solid var(--accent-rose)' : alertLevel === "Warning" ? '4px solid var(--accent-amber)' : '4px solid var(--accent-emerald)'
      }}
    >
      {/* Card Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{patient.name}</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({patient.id})</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {patient.room} • {patient.condition}
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
          <span className={`badge ${badgeClass}`}>
            {alertLevel === "Critical" && <AlertTriangle size={12} />}
            {edgeAnalysis.condition}
          </span>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            Edge Node: {patient.edge_node_id}
          </span>
        </div>
      </div>

      {/* Mini ECG Waveform Visualizer */}
      <ECGVisualizer 
        dataPoints={ecgWaveform} 
        color={ecgColor} 
        height={90} 
        label={`Live Lead II - ${edgeAnalysis.inference_latency_ms || 4.1}ms Edge AI`} 
      />

      {/* Vitals Digital Dashboard Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
        
        {/* Heart Rate */}
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-rose)', fontSize: '0.7rem', fontWeight: 600 }}>
            <span>HEART RATE</span>
            <Heart size={12} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '2px' }}>
            <span className="mono-val" style={{ fontSize: '1.4rem', color: vitals.heart_rate > 100 || vitals.heart_rate < 50 ? 'var(--accent-rose)' : '#fff' }}>
              {Math.round(vitals.heart_rate)}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>bpm</span>
          </div>
        </div>

        {/* SpO2 */}
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-cyan)', fontSize: '0.7rem', fontWeight: 600 }}>
            <span>SpO2</span>
            <Activity size={12} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '2px' }}>
            <span className="mono-val" style={{ fontSize: '1.4rem', color: vitals.spo2 < 92 ? 'var(--accent-rose)' : '#fff' }}>
              {Math.round(vitals.spo2)}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>%</span>
          </div>
        </div>

        {/* Blood Pressure */}
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-amber)', fontSize: '0.7rem', fontWeight: 600 }}>
            <span>BLOOD PRESS.</span>
            <Activity size={12} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px', marginTop: '2px' }}>
            <span className="mono-val" style={{ fontSize: '1.2rem', color: vitals.sys_bp > 140 ? 'var(--accent-amber)' : '#fff' }}>
              {Math.round(vitals.sys_bp)}/{Math.round(vitals.dia_bp)}
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>mmHg</span>
          </div>
        </div>

      </div>

      {/* Card Footer Action */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          <Cpu size={14} color="var(--accent-cyan)" />
          <span>Edge Risk: <strong style={{ color: edgeAnalysis.anomaly_score > 0.5 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>{(edgeAnalysis.anomaly_score * 100).toFixed(0)}%</strong></span>
        </div>

        <button 
          onClick={() => onSelectPatient(patient)} 
          style={{ 
            background: 'rgba(6, 182, 212, 0.12)', 
            border: '1px solid rgba(6, 182, 212, 0.3)', 
            color: 'var(--accent-cyan)', 
            padding: '6px 14px', 
            borderRadius: '6px', 
            fontSize: '0.8rem', 
            fontWeight: 600, 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            transition: 'all 0.2s ease'
          }}
        >
          View Diagnostics <ChevronRight size={14} />
        </button>
      </div>

    </div>
  );
}
