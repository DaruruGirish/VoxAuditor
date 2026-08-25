import React, { useState, useEffect } from 'react';

export default function Dashboard({ onTabSelect }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeLegend, setActiveLegend] = useState({});

  useEffect(() => {
    fetch('/api/dashboard')
      .then(res => {
        if (!res.ok) throw new Error('API server is not running or dashboard data failed to load.');
        return res.json();
      })
      .then(d => {
        setData(d);
        // Set all complaint tags active by default in legend
        const initialLegend = {};
        d.complaint_trends.forEach(t => {
          initialLegend[t.tag] = true;
        });
        setActiveLegend(initialLegend);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const toggleLegend = (tag) => {
    setActiveLegend(prev => ({
      ...prev,
      [tag]: !prev[tag]
    }));
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
        <div className="pulse-dot"></div>
        <span style={{ marginLeft: '10px', color: 'var(--text-secondary)' }}>Analyzing reviews and calculating trends...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ borderLeft: '4px solid var(--primary)', padding: '2rem', textAlign: 'center' }}>
        <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Failed to Load Data</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Please make sure the Python backend is running locally at <code style={{color: 'var(--accent)'}}>http://127.0.0.1:8000</code>.
        </div>
      </div>
    );
  }

  const { total_reviews, avg_rating, product_breakdown, complaint_trends, alerts } = data;

  // Custom SVG Chart parameters
  const chartHeight = 180;
  const chartWidth = 700;
  const paddingLeft = 40;
  const paddingRight = 30;
  const paddingTop = 20;
  const paddingBottom = 30;

  // Extract all unique months across all trends
  const allMonths = Array.from(new Set(
    complaint_trends.flatMap(t => t.monthly_data.map(m => m.month))
  )).sort();

  const maxCount = Math.max(
    ...complaint_trends.flatMap(t => t.monthly_data.map(m => m.count)),
    5 // Fallback min height scale
  );

  // Map category tag to colors
  const tagColors = {
    "Switch Melting": "#E3122B",       // Crimson
    "Blower Grinding Noise": "#ff9f0a", // Orange
    "Clicking Sound": "#00d2fc",        // Cyan
    "Wobbling Regulator": "#af52de",    // Purple
    "Filter Light Bug": "#30d158",      // Green
    "Chemical Odor": "#ffd60a",         // Yellow
    "Other Complaints": "#8e8e93"       // Gray
  };

  return (
    <div>
      {/* Metrics Row */}
      <div className="dashboard-grid">
        <div className="glass-card metric-card">
          <div className="metric-info">
            <h3>Total Reviews Ingested</h3>
            <div className="metric-value">{total_reviews}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>from fans, heaters & purifiers</div>
          </div>
          <span style={{ fontSize: '2.5rem' }}>📥</span>
        </div>

        <div className="glass-card metric-card">
          <div className="metric-info">
            <h3>Overall Brand Rating</h3>
            <div className="metric-value rating">{avg_rating} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>/ 5.0</span></div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>based on customer sentiment</div>
          </div>
          <span style={{ fontSize: '2.5rem' }}>⭐</span>
        </div>

        <div className="glass-card metric-card">
          <div className="metric-info">
            <h3>Active Anomalies</h3>
            <div className="metric-value" style={{ color: alerts.length > 0 ? 'var(--primary)' : 'var(--success)' }}>
              {alerts.length}
            </div>
            <div className="metric-trend down" style={{ background: alerts.length > 0 ? 'rgba(227,18,43,0.1)' : 'rgba(48,209,88,0.1)', color: alerts.length > 0 ? 'var(--primary)' : 'var(--success)' }}>
              {alerts.length > 0 ? 'Urgent Review Needed' : 'No Critical Spikes'}
            </div>
          </div>
          <span style={{ fontSize: '2.5rem' }}>⚠️</span>
        </div>
      </div>

      {/* Main Charts & Alerts Panel */}
      <div className="charts-section">
        {/* SVG Trend Line Chart */}
        <div className="glass-card">
          <div className="card-title">
            <div>
              Recurring Complaint Volume Trends
              <div className="card-subtitle">Monthly occurrences of grouped complaints over 12 months</div>
            </div>
          </div>

          <div className="trend-svg-container">
            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} width="100%" height="100%">
              {/* Y Axis Grid lines */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, index) => {
                const y = paddingTop + (chartHeight - paddingTop - paddingBottom) * (1 - ratio);
                const value = Math.round(ratio * maxCount);
                return (
                  <g key={index}>
                    <line x1={paddingLeft} y1={y} x2={chartWidth - paddingRight} y2={y} className="svg-grid-line" />
                    <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="svg-label">{value}</text>
                  </g>
                );
              })}

              {/* X Axis Months labels */}
              {allMonths.map((m, index) => {
                const ratio = index / (allMonths.length - 1 || 1);
                const x = paddingLeft + (chartWidth - paddingLeft - paddingRight) * ratio;
                
                // Format label: e.g. "2025-11" -> "Nov 25"
                const parts = m.split('-');
                const dateObj = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1);
                const monthStr = dateObj.toLocaleString('default', { month: 'short' });
                const yearStr = parts[0].slice(-2);

                return (
                  <g key={index}>
                    <line x1={x} y1={chartHeight - paddingBottom} x2={x} y2={chartHeight - paddingBottom + 4} stroke="rgba(255,255,255,0.2)" />
                    <text x={x} y={chartHeight - paddingBottom + 16} textAnchor="middle" className="svg-label">
                      {monthStr} '{yearStr}
                    </text>
                  </g>
                );
              })}

              {/* Drawing Paths */}
              {complaint_trends.map((trend) => {
                if (!activeLegend[trend.tag]) return null;

                // Sort monthly data matching allMonths order
                const sortedPoints = allMonths.map((m, index) => {
                  const dataPoint = trend.monthly_data.find(d => d.month === m);
                  const count = dataPoint ? dataPoint.count : 0;
                  
                  const xRatio = index / (allMonths.length - 1 || 1);
                  const x = paddingLeft + (chartWidth - paddingLeft - paddingRight) * xRatio;
                  
                  const yRatio = count / maxCount;
                  const y = paddingTop + (chartHeight - paddingTop - paddingBottom) * (1 - yRatio);
                  
                  return { x, y, count, month: m };
                });

                // Generate SVG path description
                const pathData = sortedPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                const areaData = `${pathData} L ${sortedPoints[sortedPoints.length - 1].x} ${chartHeight - paddingBottom} L ${sortedPoints[0].x} ${chartHeight - paddingBottom} Z`;
                const strokeColor = tagColors[trend.tag] || '#ffffff';

                return (
                  <g key={trend.tag}>
                    {/* Shaded Area */}
                    <path d={areaData} fill={strokeColor} className="svg-area-path" />
                    
                    {/* Trend Line */}
                    <path d={pathData} stroke={strokeColor} className="svg-line-path" />
                    
                    {/* Data Nodes */}
                    {sortedPoints.map((pt, i) => (
                      <circle
                        key={i}
                        cx={pt.x}
                        cy={pt.y}
                        r="4.5"
                        fill="#121218"
                        stroke={strokeColor}
                        className="svg-data-point"
                      >
                        <title>{`${trend.title}: ${pt.count} issues in ${pt.month}`}</title>
                      </circle>
                    ))}
                  </g>
                );
              })}

              {/* Axes lines */}
              <line x1={paddingLeft} y1={chartHeight - paddingBottom} x2={chartWidth - paddingRight} y2={chartHeight - paddingBottom} className="svg-axis-line" />
              <line x1={paddingLeft} y1={paddingTop} x2={paddingLeft} y2={chartHeight - paddingBottom} className="svg-axis-line" />
            </svg>
          </div>

          {/* Interactive Legend */}
          <div className="chart-legend">
            {complaint_trends.map(t => (
              <div 
                key={t.tag} 
                className="legend-item" 
                onClick={() => toggleLegend(t.tag)}
                style={{ opacity: activeLegend[t.tag] ? 1 : 0.4 }}
              >
                <span className="legend-color-dot" style={{ backgroundColor: tagColors[t.tag] || '#fff' }}></span>
                <span>{t.title.split(' ')[0]} {t.title.split(' ').slice(1).join(' ').toLowerCase()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Rising Anomalies Panel */}
        <div className="glass-card">
          <div className="card-title" style={{ color: 'var(--primary)' }}>
            ⚠️ Rising Anomalies
          </div>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem 1rem' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
                No active complaints have an escalating trend or low ratings.
              </div>
            ) : (
              alerts.map(a => (
                <div key={a.tag} className="alert-item">
                  <div className="alert-details">
                    <h4>{a.title}</h4>
                    <p>MoM Volume Spike: <strong style={{ color: 'var(--primary)' }}>+{a.velocity_pct}%</strong></p>
                    <p>Severity Level: <span style={{ color: 'var(--warning)' }}>★ {a.avg_rating} Avg Rating</span></p>
                  </div>
                  <span className="alert-badge">Spike</span>
                </div>
              ))
            )}
            
            {alerts.length > 0 && (
              <button 
                className="btn-pagination" 
                style={{ width: '100%', marginTop: '0.5rem', background: 'rgba(227,18,43,0.1)', borderColor: 'var(--primary)', color: 'var(--text-primary)' }}
                onClick={() => onTabSelect('chat')}
              >
                💬 Ask Agent about these alerts
              </button>
            )}
          </div>
        </div>
      </div>

      {/* MoM Velocity & Stats Table */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <div className="card-title">
          Product Category Intelligence Table
          <div className="card-subtitle">Automatic complaint grouping, volume and trend status</div>
        </div>
        
        <div className="trends-table-wrapper">
          <table className="trends-table">
            <thead>
              <tr>
                <th>Complaint Topic</th>
                <th>Total Cases</th>
                <th>Avg. Rating</th>
                <th>MoM Velocity (%)</th>
                <th>Trend Status</th>
              </tr>
            </thead>
            <tbody>
              {complaint_trends.map(t => {
                const isRising = t.status === 'Rising';
                const isFalling = t.status === 'Falling';
                const color = tagColors[t.tag] || '#fff';
                
                return (
                  <tr key={t.tag}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '4px', height: '18px', backgroundColor: color, borderRadius: '2px' }}></span>
                        <strong>{t.title}</strong>
                      </div>
                    </td>
                    <td>{t.total_count} reviews</td>
                    <td>★ {t.avg_rating}</td>
                    <td style={{ color: isRising ? 'var(--primary)' : isFalling ? 'var(--success)' : 'inherit', fontWeight: 'bold' }}>
                      {t.velocity_pct > 0 ? `+${t.velocity_pct}%` : `${t.velocity_pct}%`}
                    </td>
                    <td>
                      <span className={`status-indicator ${t.status.toLowerCase()}`}>
                        {isRising ? '📈' : isFalling ? '📉' : '➖'} {t.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Product Catalog Overview Grid */}
      <div className="glass-card">
        <div className="card-title">
          Category Sentiment Index
          <div className="card-subtitle">Volume breakdown and negative feedback rate per product line</div>
        </div>
        <div className="dashboard-grid" style={{ marginTop: '1.25rem' }}>
          {Object.entries(product_breakdown).map(([pname, stats]) => (
            <div key={pname} style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
              <h4 style={{ color: 'var(--accent)', fontSize: '1.05rem', marginBottom: '0.5rem' }}>{pname}</h4>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Review Ingestion:</span>
                <strong>{stats.count} reviews</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Avg Customer Rating:</span>
                <strong>★ {stats.avg_rating}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Negative Feedback Rate:</span>
                <strong style={{ color: stats.negative_rate_pct > 30 ? 'var(--primary)' : 'inherit' }}>
                  {stats.negative_rate_pct}%
                </strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
