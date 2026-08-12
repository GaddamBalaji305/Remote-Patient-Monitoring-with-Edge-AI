import React from 'react';
import { Activity, ShieldAlert, Cpu, Radio, Bell, RefreshCw, Zap } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, alertCount, isConnected, edgeMetrics, activePatientsCount }) {
  return (
    <header className="glass-panel" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '14px 24px', marginBottom: '24px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Brand Logo & System Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)', padding: '10px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)' }}>
            <Activity size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #93c5fd)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                RPM EDGE AI
              </h1>
              <span className="badge badge-normal" style={{ fontSize: '0.65rem' }}>
                <Zap size={10} /> EDGE-FIRST
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Remote Patient Monitoring & Low-Latency Anomaly Detection
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <button 
            onClick={() => setActiveTab('dashboard')} 
            style={{ 
              padding: '8px 16px', 
              borderRadius: '6px', 
              border: 0, 
              background: activeTab === 'dashboard' ? 'var(--accent-cyan)' : 'transparent', 
              color: activeTab === 'dashboard' ? '#000' : 'var(--text-secondary)',
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <Activity size={16} /> Patient Monitors ({activePatientsCount})
          </button>
          
          <button 
            onClick={() => setActiveTab('alerts')} 
            style={{ 
              padding: '8px 16px', 
              borderRadius: '6px', 
              border: 0, 
              background: activeTab === 'alerts' ? 'var(--accent-cyan)' : 'transparent', 
              color: activeTab === 'alerts' ? '#000' : 'var(--text-secondary)',
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              position: 'relative',
              transition: 'all 0.2s ease'
            }}
          >
            <Bell size={16} /> Alert Desk
            {alertCount > 0 && (
              <span style={{ background: 'var(--accent-rose)', color: '#fff', fontSize: '0.65rem', padding: '2px 6px', borderRadius: '10px', marginLeft: '4px' }}>
                {alertCount}
              </span>
            )}
          </button>

          <button 
            onClick={() => setActiveTab('edge')} 
            style={{ 
              padding: '8px 16px', 
              borderRadius: '6px', 
              border: 0, 
              background: activeTab === 'edge' ? 'var(--accent-cyan)' : 'transparent', 
              color: activeTab === 'edge' ? '#000' : 'var(--text-secondary)',
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <Cpu size={16} /> Edge Hardware
          </button>
        </nav>

        {/* Real-time Status Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          
          {/* WebSocket Connection Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: isConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
            <Radio size={14} className={isConnected ? "pulse" : ""} />
            <span>{isConnected ? "Live Telemetry" : "Connecting..."}</span>
          </div>

          {/* Edge Latency Pill */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(30, 41, 59, 0.8)', padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
            <Cpu size={14} color="var(--accent-cyan)" />
            <span style={{ color: 'var(--text-secondary)' }}>Edge Latency:</span>
            <span className="mono-val" style={{ color: '#fff' }}>{edgeMetrics?.inference_latency_ms || 4.2}ms</span>
          </div>

        </div>

      </div>
    </header>
  );
}
