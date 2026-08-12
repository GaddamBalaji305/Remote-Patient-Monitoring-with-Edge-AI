import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, Bell, Check, Clock } from 'lucide-react';

export default function AlertCenter({ alerts = [], onAcknowledgeAlert }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const filteredAlerts = alerts.filter(alert => {
    if (filterSeverity === 'ALL') return true;
    return alert.severity.toUpperCase() === filterSeverity;
  });

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Alert Header & Filter Bar */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '10px', borderRadius: '10px', color: 'var(--accent-rose)' }}>
            <ShieldAlert size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff' }}>Clinical Alert Desk</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Real-time Edge AI Anomaly Notifications & Triage Log</p>
          </div>
        </div>

        {/* Severity Filter Pills */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          {['ALL', 'CRITICAL', 'WARNING'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 0,
                background: filterSeverity === sev ? (sev === 'CRITICAL' ? 'var(--accent-rose)' : 'var(--accent-cyan)') : 'transparent',
                color: filterSeverity === sev ? '#000' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredAlerts.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <CheckCircle2 size={40} color="var(--accent-emerald)" style={{ marginBottom: '12px', opacity: 0.8 }} />
            <p style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>No Active Unresolved Alerts</p>
            <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>All patient telemetry is operating within normal baseline boundaries.</p>
          </div>
        ) : (
          filteredAlerts.map((alert, index) => {
            const isCritical = alert.severity === 'Critical';
            return (
              <div 
                key={alert.id || index} 
                className="glass-panel" 
                style={{ 
                  padding: '18px 24px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justify: 'space-between',
                  gap: '16px',
                  borderLeft: isCritical ? '4px solid var(--accent-rose)' : '4px solid var(--accent-amber)',
                  background: alert.acknowledged ? 'rgba(17, 24, 39, 0.4)' : 'rgba(17, 24, 39, 0.8)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                  <div style={{ 
                    background: isCritical ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)', 
                    color: isCritical ? 'var(--accent-rose)' : 'var(--accent-amber)',
                    padding: '10px',
                    borderRadius: '50%',
                    marginTop: '2px'
                  }}>
                    <AlertTriangle size={20} />
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className={`badge ${isCritical ? "badge-critical" : "badge-warning"}`}>
                        {alert.severity}
                      </span>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>{alert.title}</h4>
                    </div>

                    <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '4px' }}>
                      {alert.description}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Patient: <strong style={{ color: 'var(--text-secondary)' }}>{alert.patient_name} ({alert.patient_id})</strong></span>
                      <span>•</span>
                      <span>Node: <strong style={{ color: 'var(--text-secondary)' }}>{alert.edge_node_id}</strong></span>
                      <span>•</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> {new Date((alert.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Acknowledge Action Button */}
                <div>
                  {alert.acknowledged ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-emerald)', fontSize: '0.8rem', fontWeight: 600 }}>
                      <CheckCircle2 size={16} /> Acknowledged by {alert.acknowledged_by || "Clinician"}
                    </span>
                  ) : (
                    <button
                      onClick={() => onAcknowledgeAlert(alert.id || index)}
                      style={{
                        background: 'rgba(16, 185, 129, 0.15)',
                        border: '1px solid rgba(16, 185, 129, 0.4)',
                        color: 'var(--accent-emerald)',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <Check size={14} /> Acknowledge Alert
                    </button>
                  )}
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
