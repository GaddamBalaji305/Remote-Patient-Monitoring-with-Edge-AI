import React, { useState } from 'react';
import { Sliders, AlertCircle, Heart, Zap, RefreshCw, Radio } from 'lucide-react';

export default function SimulationControlPanel({ patients = [], onTriggerAnomaly, activeOverrides = {} }) {
  const [selectedPatientId, setSelectedPatientId] = useState(patients[0]?.id || 'PAT-101');
  const [isExpanded, setIsExpanded] = useState(true);

  const anomalyOptions = [
    { label: "Normal Baseline", value: "None", color: "#10b981" },
    { label: "Inject PVC Arrhythmia", value: "Arrhythmia", color: "#f59e0b" },
    { label: "Trigger Acute Hypoxia", value: "Hypoxia", color: "#ef4444" },
    { label: "Hypertensive Crisis", value: "Hypertension", color: "#ef4444" },
    { label: "Sensor Disconnect", value: "SensorDisconnect", color: "#6b7280" }
  ];

  const handleSimulate = (anomalyType) => {
    onTriggerAnomaly(selectedPatientId, anomalyType);
  };

  return (
    <div className="glass-panel" style={{ marginTop: '24px', padding: '16px 24px', borderTop: '2px solid var(--accent-cyan)' }}>
      
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)', padding: '8px', borderRadius: '8px' }}>
            <Sliders size={18} />
          </div>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>CLINICAL ANOMALY SIMULATION BENCH</h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Inject physiological events to test real-time Edge AI response</p>
          </div>
        </div>

        {/* Patient Selection Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Target Patient:</label>
          <select 
            value={selectedPatientId} 
            onChange={(e) => setSelectedPatientId(e.target.value)}
            style={{ 
              background: '#090d16', 
              color: '#fff', 
              border: '1px solid var(--border-color)', 
              padding: '8px 12px', 
              borderRadius: '6px', 
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {patients.map(p => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.id}) {activeOverrides[p.id] && activeOverrides[p.id] !== "None" ? `[${activeOverrides[p.id]}]` : ""}
              </option>
            ))}
          </select>
        </div>

        {/* Anomaly Trigger Buttons */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {anomalyOptions.map(opt => {
            const isActive = activeOverrides[selectedPatientId] === opt.value || (!activeOverrides[selectedPatientId] && opt.value === "None");
            return (
              <button
                key={opt.value}
                onClick={() => handleSimulate(opt.value)}
                style={{
                  padding: '7px 12px',
                  borderRadius: '6px',
                  border: isActive ? `1px solid ${opt.color}` : '1px solid var(--border-color)',
                  background: isActive ? `${opt.color}22` : 'rgba(15, 23, 42, 0.6)',
                  color: isActive ? opt.color : 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                {isActive && <Radio size={12} color={opt.color} />}
                {opt.label}
              </button>
            );
          })}
        </div>

      </div>

    </div>
  );
}
