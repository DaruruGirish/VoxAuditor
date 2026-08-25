import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import ReviewExplorer from './components/ReviewExplorer';
import AgentChat from './components/AgentChat';
import ArchitectureView from './components/ArchitectureView';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="app-container">
      {/* Premium Header */}
      <header className="app-header">
        <div className="logo-section">
          <div className="logo-badge"></div>
          <div>
            <div className="logo-text">
              Vox <span className="logo-sub">Auditor</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', letterSpacing: '0.5px', marginTop: '1px' }}>
              MARKETING & PRODUCT ANALYTICS SUITE
            </div>
          </div>
        </div>

        {/* Header Tabs Navigation */}
        <nav className="nav-tabs">
          <button 
            className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-tab-btn ${activeTab === 'explorer' ? 'active' : ''}`}
            onClick={() => setActiveTab('explorer')}
          >
            🔍 Review Explorer
          </button>
          <button 
            className={`nav-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            💬 Intelligence Agent
          </button>
          <button 
            className={`nav-tab-btn ${activeTab === 'architecture' ? 'active' : ''}`}
            onClick={() => setActiveTab('architecture')}
          >
            ⚙️ Architecture & Scale
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard onTabSelect={setActiveTab} />}
        {activeTab === 'explorer' && <ReviewExplorer />}
        {activeTab === 'chat' && <AgentChat />}
        {activeTab === 'architecture' && <ArchitectureView />}
      </main>

      {/* Subtle footer */}
      <footer style={{ padding: '1.5rem', textAlign: 'center', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(10,10,15,0.4)' }}>
        Vox Auditor • Powered by local NLP Fact-Retrieval Agents • Strictly Grounded & Hallucination-Free
      </footer>
    </div>
  );
}
