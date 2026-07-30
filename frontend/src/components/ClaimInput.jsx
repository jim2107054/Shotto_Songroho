import React, { useState, useRef } from 'react';

export default function ClaimInput({ onSubmit, loading, t, lang }) {
  const [tab, setTab] = useState('text');
  const [text, setText] = useState('');
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [url, setUrl] = useState('');
  const fileRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setImageBase64(ev.target.result);
      setImagePreview(ev.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setImageBase64(ev.target.result);
      setImagePreview(ev.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = () => {
    if (loading) return;
    const payload = { lang };
    if (tab === 'text' && text.trim()) {
      payload.text = text.trim();
    }
    if (tab === 'image' && imageBase64) {
      payload.imageBase64 = imageBase64;
      if (text.trim()) payload.text = text.trim();
    }
    if (tab === 'url' && url.trim()) {
      payload.url = url.trim();
    }

    if (!payload.text && !payload.imageBase64 && !payload.url) return;
    onSubmit(payload);
  };

  const canSubmit =
    (tab === 'text' && text.trim().length > 0) ||
    (tab === 'image' && imageBase64) ||
    (tab === 'url' && url.trim().length > 0);

  return (
    <div className="claim-input-card" id="claim-input">
      {/* Tabs */}
      <div className="input-tabs">
        <button
          className={`input-tab ${tab === 'text' ? 'active' : ''}`}
          onClick={() => setTab('text')}
          id="tab-text"
        >
          📝 {t.tab_text}
        </button>
        <button
          className={`input-tab ${tab === 'image' ? 'active' : ''}`}
          onClick={() => setTab('image')}
          id="tab-image"
        >
          🖼️ {t.tab_image}
        </button>
        <button
          className={`input-tab ${tab === 'url' ? 'active' : ''}`}
          onClick={() => setTab('url')}
          id="tab-url"
        >
          🔗 {t.tab_url}
        </button>
      </div>

      {/* Text input */}
      {tab === 'text' && (
        <textarea
          id="claim-text"
          className="claim-textarea"
          placeholder={t.placeholder_text}
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={2000}
          dir="auto"
        />
      )}

      {/* Image upload */}
      {tab === 'image' && (
        <div>
          <div
            className={`image-upload-area ${imagePreview ? 'has-image' : ''}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            id="image-upload"
          >
            {imagePreview ? (
              <div>
                <img src={imagePreview} alt="Uploaded preview" className="image-preview" />
                <p className="upload-text" style={{ marginTop: '8px' }}>
                  ✅ {t.image_uploaded || 'Image uploaded. Click to change.'}
                </p>
              </div>
            ) : (
              <div>
                <div className="upload-icon">📸</div>
                <p className="upload-text">
                  <strong>{t.upload_title}</strong><br />
                  {t.upload_desc}
                </p>
              </div>
            )}
            <input
              type="file"
              ref={fileRef}
              accept="image/*"
              onChange={handleImageChange}
              style={{ display: 'none' }}
            />
          </div>
          {/* Optional text context with image */}
          <textarea
            className="claim-textarea"
            placeholder={t.image_context_optional || 'Optional: Additional context about the image...'}
            value={text}
            onChange={(e) => setText(e.target.value)}
            style={{ marginTop: '12px', minHeight: '60px' }}
            dir="auto"
          />
        </div>
      )}

      {/* URL input */}
      {tab === 'url' && (
        <input
          id="claim-url"
          type="url"
          className="url-input"
          placeholder={t.placeholder_url}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      )}

      {/* Submit row */}
      <div className="submit-row">
        <span className="char-count">
          {tab === 'text' && `${text.length}/2000`}
        </span>
        <button
          id="submit-btn"
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              {t.submitting}
            </>
          ) : (
            <>⚡ {t.submit}</>
          )}
        </button>
      </div>
    </div>
  );
}
