import React, { useEffect, useState } from 'react';
import { verifyChain } from '../api/client';

export default function IntegrityPage({ t = {} }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    verifyChain()
      .then((data) => {
        if (active) setStatus(data);
      })
      .catch((error) => {
        console.error('Chain verification failed:', error);
        if (active) setStatus({ valid: false, errors: [error.message] });
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const proofPath = status?.latest_ots_proof?.proof_path;

  return (
    <div className="corpus-section integrity-page">
      <div className="corpus-header">
        <h1 className="corpus-title">{t.integrity_title || 'Integrity'}</h1>
        <p className="corpus-desc">
          {t.integrity_desc || 'The corpus is serialized, hashed, chained, and anchored with OpenTimestamps so edits are detectable.'}
        </p>
      </div>

      {loading ? (
        <div className="text-center" style={{ padding: '48px' }}>
          <div className="spinner" style={{ margin: '0 auto' }}></div>
        </div>
      ) : (
        <>
          <div className="integrity-metrics">
            <div className="data-card navy-card">
              <span>{t.integrity_entries || 'Chain Entries'}</span>
              <strong>{status?.chain_length || 0}</strong>
            </div>
            <div className="data-card teal-card">
              <span>{t.integrity_verif || 'Verification'}</span>
              <strong>{status?.valid ? (t.integrity_valid || 'Valid') : (t.integrity_invalid || 'Invalid')}</strong>
            </div>
            <div className="data-card orange-card">
              <span>{t.integrity_ots || 'OTS Proof'}</span>
              <strong>{status?.latest_ots_proof?.status || (t.integrity_missing || 'missing')}</strong>
            </div>
          </div>

          <div className="corpus-entry integrity-card">
            <h2>{t.integrity_hash_title || 'Current Chain Hash'}</h2>
            <code className="hash-code">{status?.chain_hash || (t.integrity_unavail || 'Unavailable')}</code>
            {proofPath && (
              <p className="integrity-copy">
                {t.integrity_latest_proof || 'Latest proof'}: <a href="/api/chain/proof/latest" target="_blank" rel="noopener noreferrer">{proofPath}</a>
              </p>
            )}
            {status?.errors?.length > 0 && (
              <div className="image-alert">
                <div className="image-alert-text">{status.errors.join('; ')}</div>
              </div>
            )}
          </div>

          <div className="corpus-entry integrity-card">
            <h2>{t.integrity_verify_yourself || 'Verify It Yourself'}</h2>
            <ol className="verify-steps">
              <li>{t.integrity_step1 || 'Run this command from the backend folder:'} <code>python -c "from app.chain.service import verify_stored_chain; print(verify_stored_chain())"</code></li>
              <li>{t.integrity_step2 || 'Confirm the reported chain hash matches the value shown here.'}</li>
              <li>{t.integrity_step3 || 'Run this command to check timestamp confirmation:'} <code>ots verify -f app/chain/current_chain_hash.txt app/chain/proofs/&lt;proof&gt;.ots</code></li>
            </ol>
          </div>
        </>
      )}
    </div>
  );
}
