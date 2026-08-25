import React from 'react';

export default function ArchitectureView() {
  return (
    <div className="architecture-layout">
      {/* Visual Flow diagram */}
      <div className="glass-card">
        <div className="card-title">
          Vox Auditor - Core System Architecture
          <div className="card-subtitle">Data flow from raw, unstructured customer reviews through vector embeddings to verified QA responses</div>
        </div>
        
        <div className="architecture-flow">
          <div className="flow-node">
            <span style={{ fontSize: '1.25rem' }}>📄</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Messy Reviews</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Amazon, Flipkart, Retail</div>
          </div>
          
          <div className="flow-arrow">➡</div>
          
          <div className="flow-node primary">
            <span className="tag-badge agent-type" style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)' }}>Agent 1</span>
            <span style={{ fontSize: '1.25rem' }}>🧹</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Ingestion & Cleaning</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Normalization / Typos</div>
          </div>
          
          <div className="flow-arrow">➡</div>
          
          <div className="flow-node primary">
            <span className="tag-badge agent-type" style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)' }}>Agent 2</span>
            <span style={{ fontSize: '1.25rem' }}>📂</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Topic Grouping</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Semantic Clustering</div>
          </div>

          <div className="flow-arrow">➡</div>

          {/* NEW: Vector DB node */}
          <div className="flow-node" style={{ borderColor: 'var(--accent)', background: 'rgba(0,210,252,0.06)' }}>
            <span className="tag-badge" style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', backgroundColor: 'rgba(0,210,252,0.2)', color: 'var(--accent)', fontSize: '0.6rem', padding: '2px 8px', borderRadius: '8px' }}>ChromaDB</span>
            <span style={{ fontSize: '1.25rem' }}>🧠</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Vector Index</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>384-dim Embeddings</div>
          </div>

          <div className="flow-arrow">➡</div>
          
          <div className="flow-node accent">
            <span className="tag-badge agent-type" style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', backgroundColor: 'rgba(0,210,252,0.15)', color: 'var(--accent)' }}>Agent 3</span>
            <span style={{ fontSize: '1.25rem' }}>🔍</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Semantic Retrieval</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Vector Search + Trends</div>
          </div>

          <div className="flow-arrow">➡</div>

          <div className="flow-node accent">
            <span className="tag-badge agent-type" style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', backgroundColor: 'rgba(0,210,252,0.15)', color: 'var(--accent)' }}>Agent 4</span>
            <span style={{ fontSize: '1.25rem' }}>🛡️</span>
            <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginTop: '0.25rem' }}>Response Synthesizer</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Factual citations</div>
          </div>
        </div>
      </div>

      {/* Detail Q&A sections */}
      <div className="arch-sections-grid">
        {/* Vector RAG Pipeline details */}
        <div className="glass-card arch-card">
          <h3>Vector RAG Pipeline (Implemented)</h3>
          <p>
            The QA agent uses a <strong>Retrieval-Augmented Generation (RAG)</strong> architecture powered by a local vector database:
          </p>
          <ul>
            <li>
              <strong>Embedding Model:</strong> <code>all-MiniLM-L6-v2</code> from sentence-transformers generates 384-dimensional vector embeddings for each review. Runs entirely locally — no API keys or cloud services needed.
            </li>
            <li>
              <strong>Vector Database:</strong> <strong>ChromaDB</strong> stores embeddings with rich metadata (product, rating, date, category). Uses HNSW index with cosine similarity for sub-millisecond search across all reviews.
            </li>
            <li>
              <strong>Query Classification:</strong> The agent automatically detects query type — <em>factual</em> ("why are heaters melting?"), <em>trend</em> ("is this getting worse?"), or <em>comparative</em> ("compare summer vs winter") — and routes to specialized handlers.
            </li>
            <li>
              <strong>Semantic Search:</strong> Instead of keyword matching, the agent finds reviews by <em>meaning</em>. Asking about "tik tok sound" correctly retrieves reviews mentioning "clicking noise" or "ticking sound" without needing exact word matches.
            </li>
            <li>
              <strong>Temporal Trend Analysis:</strong> For trend questions, the agent retrieves relevant reviews across all months, groups them chronologically, computes complaint velocity, and determines if an issue is rising, stable, or declining.
            </li>
          </ul>
        </div>

        {/* Agent Collaboration details */}
        <div className="glass-card arch-card">
          <h3>How the Agents Collaborate</h3>
          <p>
            The system separates concerns across specialized autonomous agents to deliver real-time dashboards and bulletproof Q&A:
          </p>
          <ul>
            <li>
              <strong>Ingestion Agent:</strong> Cleans raw scrapings, strips HTML, resolves product names to master SKUs, and fixes obvious spelling variations (e.g. mapping "swich" or "toggle" to standard indices) to ready the data for downstream models.
            </li>
            <li>
              <strong>Clustering Agent:</strong> Operates periodically. It clusters incoming reviews into core complaint topics using unsupervised N-Gram phrase matching and embedding similarity, and assigns a representative label.
            </li>
            <li>
              <strong>Semantic Retrieval Agent:</strong> The core of the RAG pipeline. Encodes user queries into vector embeddings, performs cosine similarity search against the ChromaDB index with metadata filters (product, rating, date range), and returns the most relevant reviews. For trend queries, it groups results by month and computes temporal direction.
            </li>
            <li>
              <strong>Response Synthesizer Agent:</strong> Receives the retrieved reviews. It compiles summaries and binds citations (e.g., <code>[Review #1]</code>). It runs validation checks to ensure no claim is made without a matching Review ID in the context.
            </li>
          </ul>
        </div>

        {/* Catalog Scalability details */}
        <div className="glass-card arch-card">
          <h3>Scaling to the Entire Product Catalog</h3>
          <p>
            The company sells thousands of SKUs (Geysers, Kitchen Appliances, Wires, Switchgears). To scale from one product line to the full product catalog, the architecture upgrades to a production-grade Big Data & AI pipeline:
          </p>
          <ul>
            <li>
              <strong>Distributed Streaming Pipeline:</strong> Ingest reviews from multiple e-commerce scrapers, website reviews, and customer care logs in real-time using <strong>Apache Kafka</strong> as the message bus, feeding to workers in a distributed queue.
            </li>
            <li>
              <strong>Hierarchical Vector Retrieval & Clustering:</strong> The ChromaDB integration demonstrated here scales to production using managed vector DBs (<strong>Pinecone</strong>, <strong>Qdrant</strong>, or <strong>Weaviate</strong>) with metadata partitioning for sub-50ms search across millions of reviews.
            </li>
            <li>
              <strong>Streaming / Mini-batch Clustering:</strong> Instead of re-clustering all historical data, use incremental streaming models (e.g., Birch or online topic modeling) that merge new complaints into existing clusters or dynamically spawn new topics when new issues appear.
            </li>
            <li>
              <strong>Query Routing Agent:</strong> Add a high-level router agent that interprets broad questions (e.g., "What appliances have fire risks?") and breaks them into parallel vector search sub-queries, routing to Space Heaters, Geysers, and Sandwich Maker indices, then merging the results.
            </li>
            <li>
              <strong>Aggregated Indexing & Caching:</strong> Pre-calculate dashboard trends and velocity metrics nightly. Store them in a high-speed cache (like <strong>Redis</strong>) so managers can load catalog trends instantly without hitting deep DB tables.
            </li>
          </ul>
        </div>
      </div>

      {/* Hallucination Prevention detail banner */}
      <div className="glass-card" style={{ borderLeft: '4px solid var(--success)', background: 'rgba(48,209,88,0.03)' }}>
        <h3 style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
          🛡️ Failsafe Hallucination Prevention Mechanism
        </h3>
        <p style={{ fontSize: '0.85rem', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
          To satisfy the <strong>Strict No-Hallucination Rule</strong>, the backend separates retrieval from text generation. The Response Synthesizer is structurally incapable of writing a claim without linking it to a verified Review ID. Vector search results are filtered by a <strong>similarity threshold (≥0.25)</strong> — if the query doesn't semantically match any reviews, the agent returns an explicit "I do not know" response rather than guessing. For unanswerable sub-questions (e.g., "Did customer care refund them?"), the agent detects the absence of matching evidence and injects a <strong>"Note on lack of details"</strong> to the answer.
        </p>
      </div>
    </div>
  );
}
