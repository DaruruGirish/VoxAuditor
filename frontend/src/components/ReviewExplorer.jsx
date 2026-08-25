import React, { useState, useEffect } from 'react';

export default function ReviewExplorer() {
  const [reviews, setReviews] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(8);
  
  // Filter States
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedRating, setSelectedRating] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchText, setSearchText] = useState('');
  
  const [loading, setLoading] = useState(true);

  // Helper to construct rating query values
  // e.g. "critical" -> "1,2"
  const getRatingValue = (type) => {
    if (type === 'critical') return '1,2';
    if (type === 'moderate') return '3';
    if (type === 'praise') return '4,5';
    return '';
  };

  const fetchReviews = () => {
    setLoading(true);
    let url = `/api/reviews?page=${page}&limit=${limit}`;
    
    if (selectedProduct) url += `&product=${encodeURIComponent(selectedProduct)}`;
    if (selectedRating) url += `&rating=${getRatingValue(selectedRating)}`;
    if (selectedCategory) url += `&category_tag=${encodeURIComponent(selectedCategory)}`;
    if (searchText) url += `&search=${encodeURIComponent(searchText)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        setReviews(data.reviews);
        setTotal(data.total);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching reviews:', err);
        setLoading(false);
      });
  };

  // Fetch whenever page or filters change
  useEffect(() => {
    fetchReviews();
  }, [page, selectedProduct, selectedRating, selectedCategory]);

  // Handle Search submit / debounce
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReviews();
  };

  const resetFilters = () => {
    setSelectedProduct('');
    setSelectedRating('');
    setSelectedCategory('');
    setSearchText('');
    setPage(1);
  };

  // Helper to render rating stars
  const renderStars = (rating) => {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  // Helper to highlight terms or snippet in review text
  const highlightText = (text, snippet) => {
    if (!snippet || snippet.length < 8) return text;
    
    // Attempt to locate snippet in text (ignoring formatting / small deviations)
    const index = text.toLowerCase().indexOf(snippet.toLowerCase().slice(0, 30));
    if (index !== -1) {
      const matchLength = Math.min(snippet.length, text.length - index);
      const start = text.slice(0, index);
      const match = text.slice(index, index + matchLength);
      const end = text.slice(index + matchLength);
      
      return (
        <>
          {start}
          <span className="highlight-snippet">{match}</span>
          {end}
        </>
      );
    }
    
    return text;
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div>
      <div className="explorer-header">
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Raw Review Explorer</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Filter and read full transcripts of customer feedback. Red highlights represent detected complaints.
          </p>
        </div>
        <button className="btn-pagination" onClick={resetFilters}>
          🔄 Reset Filters
        </button>
      </div>

      {/* Filter Control Box */}
      <div className="filters-panel">
        <div className="filter-group">
          <label>Product Catalog</label>
          <select 
            className="custom-select"
            value={selectedProduct}
            onChange={(e) => { setSelectedProduct(e.target.value); setPage(1); }}
          >
            <option value="">All Products</option>
            <option value="Space Heater">Space Heater</option>
            <option value="Ceiling Fan">Ceiling Fan</option>
            <option value="Air Purifier">Air Purifier</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Sentiment Tier</label>
          <select 
            className="custom-select"
            value={selectedRating}
            onChange={(e) => { setSelectedRating(e.target.value); setPage(1); }}
          >
            <option value="">All Ratings</option>
            <option value="critical">Critical (1-2 Stars)</option>
            <option value="moderate">Moderate (3 Stars)</option>
            <option value="praise">Positive (4-5 Stars)</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Grouped Complaint Tag</label>
          <select 
            className="custom-select"
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
          >
            <option value="">All Complaint Tags</option>
            <option value="Switch Melting">Switch Melting (Heaters)</option>
            <option value="Blower Grinding Noise">Blower Noise (Heaters)</option>
            <option value="Clicking Sound">Clicking Sound (Fans)</option>
            <option value="Wobbling Regulator">Wobbling / Shaking (Fans)</option>
            <option value="Filter Light Bug">Filter Light Bug (Purifiers)</option>
            <option value="Chemical Odor">Chemical Odor (Purifiers)</option>
            <option value="Praise">Praise / No Issue</option>
            <option value="Other Complaints">Other Issues</option>
          </select>
        </div>

        <div className="filter-group" style={{ minWidth: '220px' }}>
          <label>Text Search</label>
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
            <input 
              type="text" 
              className="custom-input" 
              placeholder="Search words (e.g. burn)..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn-pagination" style={{ padding: '0.65rem' }}>
              🔍
            </button>
          </form>
        </div>
      </div>

      {/* Review Cards Grid */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <div className="pulse-dot"></div>
          <span style={{ marginLeft: '10px', color: 'var(--text-secondary)' }}>Retrieving reviews from database...</span>
        </div>
      ) : reviews.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📭</div>
          <h3>No Reviews Match Your Criteria</h3>
          <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>Try broadening your search text or removing filters.</p>
        </div>
      ) : (
        <div className="reviews-grid">
          {reviews.map(r => (
            <div key={r.review_id} className="review-card-item">
              <div className="review-card-header">
                <div className="review-meta">
                  <span className="reviewer-name">{r.reviewer}</span>
                  <span className="review-date">{r.date}</span>
                  <span className="review-tag" style={{ 
                    backgroundColor: r.category_tag === 'Praise' ? 'rgba(48,209,88,0.1)' : 
                                    r.category_tag === 'Other Complaints' ? 'rgba(255,255,255,0.06)' : 
                                    'rgba(227,18,43,0.08)',
                    color: r.category_tag === 'Praise' ? 'var(--success)' : 
                           r.category_tag === 'Other Complaints' ? 'var(--text-secondary)' : 
                           'var(--primary-hover)'
                  }}>
                    {r.category_tag}
                  </span>
                </div>
                <div className="review-rating-stars">
                  {renderStars(r.rating)}
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Product: <strong style={{ color: 'var(--text-primary)' }}>{r.product}</strong> ({r.model}) | ID: {r.review_id}
              </div>
              <p className="review-text-content">
                {highlightText(r.text, r.complaint_snippet)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Footer */}
      {!loading && reviews.length > 0 && (
        <div className="explorer-footer">
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Showing <strong>{reviews.length}</strong> of <strong>{total}</strong> reviews (Page {page} of {totalPages})
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              className="btn-pagination" 
              disabled={page === 1}
              onClick={() => setPage(prev => Math.max(prev - 1, 1))}
            >
              ◀ Previous
            </button>
            <button 
              className="btn-pagination" 
              disabled={page >= totalPages}
              onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
            >
              Next ▶
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
