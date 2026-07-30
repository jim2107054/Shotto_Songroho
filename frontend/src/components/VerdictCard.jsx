import React, { useState } from 'react';
import { VERDICT_CONFIG } from '../utils/constants';

export default function VerdictCard({ result, onReset, t }) {
  const [showPipeline, setShowPipeline] = useState(false);

  if (!result) return null;

  const vc = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.unverifiable;
  const verdictLabel = t[`verdict_${result.verdict}`] || result.verdict;
  const confidencePct = Math.round((result.confidence || 0) * 100);

  return (
    <div className="verdict-section">
      <button className="back-btn" onClick={onReset} id="back-btn">
        {t.back_to_verify}
      </button>

      <div className="verdict-card" id="verdict-card">
        {/* Verdict Header */}
        <div className={`verdict-header ${vc.bgClass}`}>
          <div className={`verdict-badge ${vc.bgClass}`}>
            <span className="verdict-badge-icon">{vc.icon}</span>
            {verdictLabel}
          </div>

          <div className="confidence-meter">
            <span className="confidence-label">{t.confidence}:</span>
            <div className="confidence-bar-bg">
              <div
                className={`confidence-bar-fill ${vc.bgClass}`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
            <span className="confidence-label">{confidencePct}%</span>
          </div>
        </div>

        {/* Image Reuse Alert */}
        {result.image_match?.matched && (
          <div className="image-alert">
            <span className="image-alert-icon">🚨</span>
            <div className="image-alert-text">
              <strong>{t.image_reuse_alert}</strong><br />
              {t.image_reuse_desc}<br />
              {t.image_original}: {result.image_match.original_source}
              {result.image_match.original_date && ` (${result.image_match.original_date})`}
              {result.image_match.original_context && (
                <span> — {result.image_match.original_context}</span>
              )}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="verdict-summary">
          {result.summary}
        </div>

        {/* Sources */}
        {result.sources?.length > 0 && (
          <div className="sources-section">
            <h3 className="sources-title">
              📚 {t.sources_title} ({result.sources.length})
            </h3>
            {result.sources.map((source, idx) => (
              <div key={idx} className="source-card">
                {source.source_org && (
                  <div className="source-org">{source.source_org}</div>
                )}
                <div className="source-title">{source.title}</div>
                {source.excerpt && (
                  <div className="source-excerpt">{source.excerpt}</div>
                )}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    🔗 {t.source} →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Pipeline Steps Detail */}
        {result.pipeline_steps?.length > 0 && (
          <div className="pipeline-detail">
            <button
              className="pipeline-toggle"
              onClick={() => setShowPipeline(!showPipeline)}
              id="pipeline-toggle"
            >
              <span className={`pipeline-toggle-arrow ${showPipeline ? 'open' : ''}`}>▼</span>
              {showPipeline ? t.pipeline_hide : t.pipeline_show}
            </button>

            {showPipeline && (
              <div className="pipeline-detail-content">
                {result.pipeline_steps.map((step, idx) => (
                  <div key={idx} className="pipeline-detail-step">
                    <span className="detail-status">
                      {step.status === 'completed' ? '✅' :
                       step.status === 'failed' ? '❌' :
                       step.status === 'skipped' ? '⏭️' : '⏳'}
                    </span>
                    <div>
                      <span className="detail-agent">{step.agent}</span>
                      {step.summary && (
                        <span className="detail-summary"> — {step.summary}</span>
                      )}
                      {step.duration_ms != null && (
                        <span className="detail-duration"> ({step.duration_ms}ms)</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
