import React, { useEffect, useState } from 'react';
import { verifyChain } from '../api/client';

export default function IntegrityPage() {
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
        <h1 className="corpus-title">Integrity</h1>
        <p className="corpus-desc">
          The corpus is serialized, hashed, chained, and anchored with OpenTimestamps so edits are detectable.
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
              <span>Chain Entries</span>
              <strong>{status?.chain_length || 0}</strong>
            </div>
            <div className="data-card teal-card">
              <span>Verification</span>
              <strong>{status?.valid ? 'Valid' : 'Invalid'}</strong>
            </div>
            <div className="data-card orange-card">
              <span>OTS Proof</span>
              <strong>{status?.latest_ots_proof?.status || 'missing'}</strong>
            </div>
          </div>

          <div className="corpus-entry integrity-card">
            <h2>Current Chain Hash</h2>
            <code className="hash-code">{status?.chain_hash || 'Unavailable'}</code>
            {proofPath && (
              <p className="integrity-copy">
                Latest proof: <a href="/api/chain/proof/latest" target="_blank" rel="noopener noreferrer">{proofPath}</a>
              </p>
            )}
            {status?.errors?.length > 0 && (
              <div className="image-alert">
                <div className="image-alert-text">{status.errors.join('; ')}</div>
              </div>
            )}
          </div>

          <div className="corpus-entry integrity-card">
            <h2>Verify It Yourself</h2>
            <ol className="verify-steps">
              <li>Run <code>python -c "from app.chain.service import verify_stored_chain; print(verify_stored_chain())"</code> from the backend folder.</li>
              <li>Confirm the reported chain hash matches the value shown here.</li>
              <li>Run <code>ots verify -f app/chain/current_chain_hash.txt app/chain/proofs/&lt;proof&gt;.ots</code> to check timestamp confirmation.</li>
            </ol>
          </div>
        </>
      )}
    </div>
  );
}
