import React, { useState, useEffect, useCallback } from 'react';
import { searchCorpus } from '../api/client';

export default function CorpusBrowser({ lang, t }) {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const ITEMS_PER_PAGE = 12;

  const fetchCorpus = useCallback(async () => {
    setLoading(true);
    try {
      const data = await searchCorpus({
        query: query || undefined,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        verdictLabel: verdictFilter || undefined,
        limit: 100,
      });
      setEntries(data.results || []);
      setTotal(data.total || 0);
      setCurrentPage(1);
    } catch (err) {
      console.error('Corpus fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, [query, dateFrom, dateTo, verdictFilter]);

  useEffect(() => {
    fetchCorpus();
  }, [fetchCorpus]);

  // Debounced search
  const [searchTimeout, setSearchTimeout] = useState(null);
  const handleSearchChange = (value) => {
    setQuery(value);
    if (searchTimeout) clearTimeout(searchTimeout);
    setSearchTimeout(setTimeout(fetchCorpus, 500));
  };

  const totalPages = Math.max(1, Math.ceil(entries.length / ITEMS_PER_PAGE));
  const paginatedEntries = entries.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="corpus-section">
      <div className="corpus-header">
        <h1 className="corpus-title">📜 {t.corpus_title}</h1>
        <p className="corpus-desc">{t.corpus_desc}</p>
      </div>

      {/* Filters */}
      <div className="corpus-filters">
        <input
          type="text"
          className="filter-input"
          placeholder={t.search_placeholder}
          value={query}
          onChange={(e) => handleSearchChange(e.target.value)}
          id="corpus-search"
          dir="auto"
        />
        <input
          type="date"
          className="filter-input"
          placeholder={t.filter_date_from}
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          id="corpus-date-from"
        />
        <input
          type="date"
          className="filter-input"
          placeholder={t.filter_date_to}
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          id="corpus-date-to"
        />
        <select
          className="filter-select"
          value={verdictFilter}
          onChange={(e) => setVerdictFilter(e.target.value)}
          id="corpus-verdict-filter"
        >
          <option value="">{t.filter_all}</option>
          <option value="verified">{t.filter_verified}</option>
          <option value="disputed">{t.filter_disputed || 'Disputed'}</option>
          <option value="false_claim">{t.filter_false}</option>
        </select>
      </div>

      <div className="corpus-count">
        {t.showing_results.replace('{count}', total)}
        {totalPages > 1 && (
          <span className="pagination-info">
            {' — ' + (t.pagination_info || 'Page {page} of {pages} ({count} total)')
              .replace('{page}', currentPage)
              .replace('{pages}', totalPages)
              .replace('{count}', total)}
          </span>
        )}
      </div>

      {/* Entries */}
      {loading ? (
        <div className="text-center" style={{ padding: '48px' }}>
          <div className="spinner" style={{ margin: '0 auto' }}></div>
        </div>
      ) : entries.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <div className="empty-state-text">{t.no_results}</div>
        </div>
      ) : (
        <>
          <div className="corpus-grid">
            {paginatedEntries.map((entry) => (
              <div key={entry.id} className="corpus-entry">
                <div className="corpus-entry-header">
                  {entry.event_date && (
                    <span className="corpus-date">📅 {entry.event_date}</span>
                  )}
                  {entry.location && (
                    <span className="corpus-location">📍 {entry.location}</span>
                  )}
                  <span className={`corpus-verdict-tag ${entry.verdict_label}`}>
                    {entry.verdict_label === 'verified' ? (t.verdict_verified || 'Verified') : entry.verdict_label === 'disputed' ? (t.verdict_disputed || 'Disputed') : (t.verdict_false_claim || 'False Claim')}
                  </span>
                </div>
                <div className="corpus-description" dir="auto">
                  {lang === 'bn' && entry.description_bn ? entry.description_bn : entry.description_en}
                </div>
                {entry.sources?.length > 0 && (
                  <div className="corpus-source">
                    {t.source || 'Source'}: {entry.sources[0].source_org || entry.sources[0].title}
                    {entry.sources[0].url && (
                      <a href={entry.sources[0].url} target="_blank" rel="noopener noreferrer">
                        {t.open_link || 'Open'}
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="corpus-pagination">
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                aria-label="Previous page"
              >
                ‹ {t.pagination_prev || 'Prev'}
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  className={`pagination-btn ${page === currentPage ? 'active' : ''}`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              ))}
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                aria-label="Next page"
              >
                {t.pagination_next || 'Next'} ›
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
