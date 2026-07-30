import React, { useCallback, useEffect, useState } from 'react';
import { accountabilityIndex } from '../api/client';

export default function AccountabilityIndex({ t }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [location, setLocation] = useState('');

  const fetchIndex = useCallback(async () => {
    setLoading(true);
    try {
      const data = await accountabilityIndex({
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        location: location || undefined,
      });
      setEntries(data.results || []);
    } catch (err) {
      console.error('Accountability index fetch failed:', err);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, location]);

  useEffect(() => {
    fetchIndex();
  }, [fetchIndex]);

  return (
    <div className="corpus-section">
      <div className="corpus-header">
        <h1 className="corpus-title">Accountability Index</h1>
        <p className="corpus-desc">
          Cited documented incidents grouped only by org/unit entities already present in source-backed corpus entries.
        </p>
      </div>

      <div className="corpus-filters">
        <input
          type="date"
          className="filter-input"
          value={dateFrom}
          onChange={(event) => setDateFrom(event.target.value)}
          aria-label="Date from"
        />
        <input
          type="date"
          className="filter-input"
          value={dateTo}
          onChange={(event) => setDateTo(event.target.value)}
          aria-label="Date to"
        />
        <input
          type="text"
          className="filter-input"
          placeholder={t.filter_location || 'Location'}
          value={location}
          onChange={(event) => setLocation(event.target.value)}
        />
      </div>

      <div className="corpus-count">Showing {entries.length} entities</div>

      {loading ? (
        <div className="text-center" style={{ padding: '48px' }}>
          <div className="spinner" style={{ margin: '0 auto' }}></div>
        </div>
      ) : entries.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">AI</div>
          <div className="empty-state-text">No cited human-rights-org incidents match these filters.</div>
        </div>
      ) : (
        <div className="corpus-grid">
          {entries.map((entry) => (
            <div key={entry.entity} className="corpus-entry accountability-entry">
              <div className="corpus-entry-header">
                <span className="corpus-verdict-tag disputed">{entry.entity}</span>
                <span className="corpus-location">{entry.incidents.length} incident(s)</span>
              </div>
              {entry.incidents.map((incident) => (
                <div key={incident.id} className="accountability-incident">
                  <div className="corpus-entry-header">
                    {incident.date && <span className="corpus-date">{incident.date}</span>}
                    {incident.location && <span className="corpus-location">{incident.location}</span>}
                  </div>
                  <div className="corpus-description">{incident.description}</div>
                  {incident.sources?.map((source, index) => (
                    <div key={`${incident.id}-${index}`} className="corpus-source">
                      Source: {source.source_org || source.title}
                      {source.url && (
                        <a href={source.url} target="_blank" rel="noopener noreferrer">Open</a>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
