import React, { useState } from 'react';
import { submitTestimony } from '../api/client';

export default function TestimonyForm({ lang }) {
  const [text, setText] = useState('');
  const [contact, setContact] = useState('');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (text.trim().length < 10) return;
    setLoading(true);
    setStatus(null);
    try {
      const result = await submitTestimony({ text: text.trim(), contactOptional: contact.trim(), lang });
      setStatus(`Queued for review: ${result.id}`);
      setText('');
      setContact('');
    } catch (error) {
      setStatus(error.message || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="corpus-section testimony-page">
      <div className="corpus-header">
        <h1 className="corpus-title">Submit Testimony</h1>
        <p className="corpus-desc">
          Submissions enter a moderation queue and are reviewed before publication. They are never added to the public corpus automatically.
        </p>
      </div>

      <form className="claim-input-card testimony-form" onSubmit={handleSubmit}>
        <label className="form-label" htmlFor="testimony-text">Your account or evidence description</label>
        <textarea
          id="testimony-text"
          className="claim-textarea"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Describe what you witnessed, where, when, and what public source or evidence can support it."
          maxLength={5000}
          dir="auto"
        />

        <label className="form-label" htmlFor="testimony-contact">Contact (optional)</label>
        <input
          id="testimony-contact"
          className="url-input"
          value={contact}
          onChange={(event) => setContact(event.target.value)}
          placeholder="Email, Signal, or another way for moderators to follow up"
        />

        <div className="submit-row">
          <span className="char-count">{text.length}/5000</span>
          <button className="submit-btn" type="submit" disabled={loading || text.trim().length < 10}>
            {loading ? 'Submitting...' : 'Submit for Review'}
          </button>
        </div>
        {status && <div className="corpus-count testimony-status">{status}</div>}
      </form>
    </div>
  );
}
