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
          <option value="false_claim">{t.filter_false}</option>
        </select>
      </div>

      <div className="corpus-count">
        {t.showing_results.replace('{count}', total)}
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
        <div className="corpus-grid">
          {entries.map((entry) => (
            <div key={entry.id} className="corpus-entry">
              <div className="corpus-entry-header">
                {entry.event_date && (
                  <span className="corpus-date">📅 {entry.event_date}</span>
                )}
                {entry.location && (
                  <span className="corpus-location">📍 {entry.location}</span>
                )}
                <span className={`corpus-verdict-tag ${entry.verdict_label}`}>
                  {entry.verdict_label === 'verified' ? 'Verified' : entry.verdict_label === 'disputed' ? 'Disputed' : 'False Claim'}
                </span>
              </div>
              <div className="corpus-description" dir="auto">
                {lang === 'bn' && entry.description_bn ? entry.description_bn : entry.description_en}
              </div>
              {entry.sources?.length > 0 && (
                <div className="corpus-source">
                  Source: {entry.sources[0].source_org || entry.sources[0].title}
                  {entry.sources[0].url && (
                    <a href={entry.sources[0].url} target="_blank" rel="noopener noreferrer">
                      Open
                    </a>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
