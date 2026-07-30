import React from 'react';

export default function Header({ lang, setLang, view, setView, t }) {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="header-brand">
          <div className="header-logo">🔍</div>
          <div>
            <div className="header-title">
              {lang === 'bn' ? t.app_name_bn : t.app_name}
            </div>
            <div className="header-subtitle">{t.tagline}</div>
          </div>
        </div>

        <div className="header-nav">
          <button
            id="nav-verify"
            className={`nav-btn ${view === 'verify' ? 'active' : ''}`}
            onClick={() => setView('verify')}
          >
            {t.nav_verify}
          </button>
          <button
            id="nav-corpus"
            className={`nav-btn ${view === 'corpus' ? 'active' : ''}`}
            onClick={() => setView('corpus')}
          >
            {t.nav_corpus}
          </button>
          <button
            id="nav-accountability"
            className={`nav-btn ${view === 'accountability' ? 'active' : ''}`}
            onClick={() => setView('accountability')}
          >
            Index
          </button>

          <button
            id="nav-integrity"
            className={`nav-btn ${view === 'integrity' ? 'active' : ''}`}
            onClick={() => setView('integrity')}
          >
            Integrity
          </button>
          <button
            id="nav-testimony"
            className={`nav-btn ${view === 'testimony' ? 'active' : ''}`}
            onClick={() => setView('testimony')}
          >
            Testimony
          </button>
          <div className="lang-toggle">
            <button
              id="lang-en"
              className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => setLang('en')}
            >
              EN
            </button>
            <button
              id="lang-bn"
              className={`lang-btn ${lang === 'bn' ? 'active' : ''}`}
              onClick={() => setLang('bn')}
            >
              বাং
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
