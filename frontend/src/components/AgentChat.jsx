import React, { useState, useRef, useEffect } from 'react';

const SUGGESTED_QUESTIONS = [
  "Is the switch melting issue getting worse over time?",
  "Why are customers mad about space heaters?",
  "Are fan clicking complaints rising or declining?",
  "What is the trend for chemical smell complaints?",
  "Why are ceiling fans wobbly?",
  "What's the main issue with air purifiers in winter?"
];

export default function AgentChat() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'agent',
      text: "Hello! I am the Vox Auditor Agent. You can ask me any question about customer reviews (e.g. specific product defects, seasonal patterns, or sentiment trends). I am strictly bound by a **No-Hallucination Guardrail**—if the data isn't in the reviews, I will tell you frankly.",
      citations: [],
      execution_steps: ["Agent initialized successfully.", "Awaiting user query."]
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentReasoning, setCurrentReasoning] = useState([]);
  const [currentCitations, setCurrentCitations] = useState([]);
  const [highlightedCitationId, setHighlightedCitationId] = useState(null);

  const messagesEndRef = useRef(null);
  const citationRefs = useRef({});

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = (textToSend) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);
    setCurrentReasoning(["[Agent] Parsing query parameters...", "[Agent] Searching indexing system..."]);
    setCurrentCitations([]);
    setHighlightedCitationId(null);

    // Call Backend QA API
    fetch('/api/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    })
      .then(res => res.json())
      .then(data => {
        const agentMsg = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          text: data.answer,
          citations: data.citations,
          execution_steps: data.execution_steps,
          isErrorMode: data.citations.length === 0 && data.answer.includes("I do not know")
        };
        setMessages(prev => [...prev, agentMsg]);
        setCurrentReasoning(data.execution_steps);
        setCurrentCitations(data.citations);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error querying QA agent:', err);
        const errorMsg = {
          id: `agent-err-${Date.now()}`,
          sender: 'agent',
          text: "I encountered an error querying the backend server. Please verify the Python backend API is running locally.",
          citations: [],
          execution_steps: ["API connection failure", err.message]
        };
        setMessages(prev => [...prev, errorMsg]);
        setLoading(false);
      });
  };

  // Clicking on citation in message bubble
  const handleCitationClick = (reviewId) => {
    setHighlightedCitationId(reviewId);
    // Scroll citation card in sidebar into view
    const cardEl = citationRefs.current[reviewId];
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Render citation tags in response text: e.g., Replace [Review #1] with styled tags
  const renderFormattedText = (text) => {
    // Split by citation brackets like [Review #1]
    const parts = text.split(/(\[Review #\d+\])/g);
    
    return parts.map((part, index) => {
      const match = part.match(/\[Review #(\d+)\]/);
      if (match) {
        const citationNum = parseInt(match[1]);
        // Find matching review in current citations
        const matchingReview = currentCitations.find(c => c.citation_number === citationNum);
        if (matchingReview) {
          return (
            <span 
              key={index} 
              className="citation-tag"
              onClick={() => handleCitationClick(matchingReview.review_id)}
            >
              #{citationNum}
            </span>
          );
        }
      }
      
      // Parse markdown-like bolding **text**
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bp, bIdx) => {
        if (bp.startsWith('**') && bp.endsWith('**')) {
          return <strong key={bIdx}>{bp.slice(2, -2)}</strong>;
        }
        return bp;
      });
    });
  };

  // Select a message to view its steps and citations in the side panel
  const handleSelectMessage = (msg) => {
    if (msg.sender === 'agent') {
      setCurrentReasoning(msg.execution_steps || []);
      setCurrentCitations(msg.citations || []);
      setHighlightedCitationId(null);
    }
  };

  return (
    <div className="chat-layout">
      {/* Central Chat Screen */}
      <div className="chat-room">
        <div className="chat-header-bar">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Voice Agent Interface</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Factual synthesis & citation mapping engine</span>
          </div>
          <div className="agent-status-pulse">
            <span className="pulse-dot"></span>
            Agent Online
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((m) => (
            <div 
              key={m.id} 
              className={`chat-bubble ${m.sender} ${m.isErrorMode ? 'error-mode' : ''}`}
              onClick={() => handleSelectMessage(m)}
              style={{ cursor: m.sender === 'agent' ? 'pointer' : 'default' }}
              title={m.sender === 'agent' ? 'Click to reload reasoning logs' : ''}
            >
              {m.sender === 'agent' ? (
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', justifyContent: 'space-between' }}>
                    <span>VOX AUDITOR AGENT</span>
                    {m.isErrorMode && <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>⛔ HALLUCINATION BLOCKED</span>}
                  </div>
                  <div style={{ whiteSpace: 'pre-line' }}>{renderFormattedText(m.text)}</div>
                </div>
              ) : (
                m.text
              )}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble agent">
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>AGENT THINKING...</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div className="pulse-dot"></div>
                <span style={{ fontStyle: 'italic', fontSize: '0.85rem' }}>Querying vector index, computing semantic similarity, binding citations...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts Row */}
        <div style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.015)', borderTop: '1px solid var(--border-color)', overflowX: 'auto', display: 'flex', gap: '0.5rem', whiteSpace: 'nowrap' }}>
          {SUGGESTED_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              className="btn-pagination"
              style={{ fontSize: '0.75rem', borderRadius: '12px', padding: '0.4rem 0.8rem', background: 'rgba(0, 210, 252, 0.05)', borderColor: 'rgba(0, 210, 252, 0.15)' }}
              disabled={loading}
              onClick={() => handleSend(q)}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          <input 
            type="text" 
            className="chat-input-box" 
            placeholder="Type your question about customer complaints (e.g. Why are fans clicking in speed 3?)..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
            disabled={loading}
          />
          <button 
            className="btn-send" 
            onClick={() => handleSend()}
            disabled={loading || !inputText.trim()}
          >
            Ask Agent
          </button>
        </div>
      </div>

      {/* Side Panels: Reasoning and Citations */}
      <div className="chat-sidebar">
        {/* Step-by-Step Reasoning */}
        <div className="sidebar-panel" style={{ flex: 0.8 }}>
          <div className="sidebar-title">Agent Execution Steps</div>
          <div className="reasoning-log-container">
            {currentReasoning.length === 0 ? (
              <span style={{ color: 'var(--text-muted)' }}>Select an agent message to inspect execution logic.</span>
            ) : (
              currentReasoning.map((step, idx) => (
                <div key={idx} className="reasoning-step">
                  <span className="step-bullet">&gt;</span>
                  <span>{step}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Source Citations */}
        <div className="sidebar-panel" style={{ flex: 1.2 }}>
          <div className="sidebar-title">Evidence Citations ({currentCitations.length})</div>
          <div className="citations-container">
            {currentCitations.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem 1rem', fontSize: '0.8rem' }}>
                📖 Citations will appear here when the agent answers using raw review references.
              </div>
            ) : (
              currentCitations.map((c) => {
                const isHighlighted = highlightedCitationId === c.review_id;
                return (
                  <div 
                    key={c.review_id}
                    ref={el => citationRefs.current[c.review_id] = el}
                    className={`citation-card ${isHighlighted ? 'highlighted' : ''}`}
                  >
                    <div className="citation-card-header">
                      <span className="citation-card-num">Citation #{c.citation_number}</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>Rating: {c.rating}/5</span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--accent)', fontWeight: 600 }}>
                      {c.product} ({c.model}) | ID: {c.review_id}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      Reviewer: {c.reviewer} | Date: {c.date}
                    </div>
                    <p className="citation-text">
                      "{c.text}"
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
