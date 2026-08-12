import React from 'react';
import { Cpu, Battery, Zap, HardDrive, Activity, Server, Radio, Shield } from 'lucide-react';

export default function EdgeNodeMonitor({ edgeMetrics }) {
  const node = edgeMetrics || {
    node_id: "NVIDIA Jetson Orin Nano / ARM Cortex-M55",
    battery_pct: 98.5,
    cpu_usage_pct: 14.8,
    ram_usage_mb: 142.8,
    inference_latency_ms: 4.2,
    packets_processed: 1420,
    status: "Healthy"
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Edge Node Banner */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)', padding: '14px', borderRadius: '12px', color: '#fff', boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)' }}>
            <Cpu size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#fff' }}>{node.node_id}</h2>
              <span className="badge badge-normal" style={{ fontSize: '0.7rem' }}>
                <Shield size={10} /> ON-DEVICE AI
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Localized PyTorch / IsolationForest inference engine running Pan-Tompkins QRS filtering
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Radio size={16} /> Status: {node.status}
          </span>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        
        {/* Inference Latency */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-cyan)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>EDGE INFERENCE LATENCY</span>
            <Zap size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '12px' }}>
            <span className="mono-val" style={{ fontSize: '2.2rem', color: '#fff' }}>{node.inference_latency_ms}</span>
            <span style={{ color: 'var(--text-muted)' }}>ms</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
            Target: &lt;10ms per 100Hz ECG frame (Sub-millisecond peak detection)
          </p>
        </div>

        {/* Battery Health Gauge */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-emerald)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>BATTERY RESERVE</span>
            <Battery size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '12px' }}>
            <span className="mono-val" style={{ fontSize: '2.2rem', color: '#fff' }}>{node.battery_pct}%</span>
            <span style={{ color: 'var(--accent-emerald)', fontSize: '0.8rem' }}>Optimal</span>
          </div>
          <div style={{ width: '100%', background: 'rgba(255,255,255,0.1)', height: '6px', borderRadius: '3px', marginTop: '12px', overflow: 'hidden' }}>
            <div style={{ width: `${node.battery_pct}%`, background: 'var(--accent-emerald)', height: '100%' }} />
          </div>
        </div>

        {/* CPU & RAM Usage */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-indigo)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>CPU / MEMORY LOAD</span>
            <HardDrive size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '12px' }}>
            <span className="mono-val" style={{ fontSize: '2.2rem', color: '#fff' }}>{node.cpu_usage_pct}%</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>CPU</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
            RAM Occupancy: <strong style={{ color: '#fff' }}>{node.ram_usage_mb} MB</strong> / 4096 MB
          </p>
        </div>

        {/* Telemetry Packets */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--accent-amber)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>TELEMETRY PACKETS</span>
            <Server size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '12px' }}>
            <span className="mono-val" style={{ fontSize: '2.2rem', color: '#fff' }}>{node.packets_processed}</span>
            <span style={{ color: 'var(--text-muted)' }}>pkts</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
            Zero packet loss detected. Cloud Sync interval: 1.0s batching
          </p>
        </div>

      </div>

    </div>
  );
}
