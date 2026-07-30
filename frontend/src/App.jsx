import React, { useState, useMemo } from 'react';
import Header from './components/Header';
import ClaimInput from './components/ClaimInput';
import LoadingPipeline from './components/LoadingPipeline';
import VerdictCard from './components/VerdictCard';
import CorpusBrowser from './components/CorpusBrowser';
import { useVerify } from './hooks/useVerify';
import enStrings from './i18n/en.json';
import bnStrings from './i18n/bn.json';

const translations = { en: enStrings, bn: bnStrings };

export default function App() {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('shotto-lang') || 'en';
  });
  const [view, setView] = useState('verify');
  const { loading, result, error, activeStep, verify, reset } = useVerify();

  const t = useMemo(() => translations[lang] || translations.en, [lang]);

  const handleLangChange = (newLang) => {
    setLang(newLang);
    localStorage.setItem('shotto-lang', newLang);
  };

  const handleSubmit = (payload) => {
    verify(payload);
  };

  const handleReset = () => {
    reset();
  };

  return (
    <div data-lang={lang}>
      <Header
        lang={lang}
        setLang={handleLangChange}
        view={view}
        setView={setView}
        t={t}
      />

      <main className="page">
        <div className="container">
          {view === 'verify' && (
            <>
              {/* Show hero + input when no result */}
              {!result && !loading && (
                <>
                  <div className="hero">
                    <h1 className="hero-title">{t.hero_title}</h1>
                    <p className="hero-desc">{t.hero_desc}</p>
                  </div>

                  <ClaimInput
                    onSubmit={handleSubmit}
                    loading={loading}
                    t={t}
                    lang={lang}
                  />

                  {error && (
                    <div style={{
                      marginTop: '16px',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      color: '#ef4444',
                      fontSize: '0.9rem',
                    }}>
                      ❌ {error}
                    </div>
                  )}
                </>
              )}

              {/* Loading pipeline animation */}
              {loading && (
                <LoadingPipeline activeStep={activeStep} t={t} />
              )}

              {/* Result */}
              {result && (
                <VerdictCard result={result} onReset={handleReset} t={t} />
              )}
            </>
          )}

          {view === 'corpus' && (
            <CorpusBrowser lang={lang} t={t} />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '24px',
        color: 'var(--text-muted)',
        fontSize: '0.8rem',
        borderTop: '1px solid var(--border-subtle)',
      }}>
        {lang === 'bn'
          ? 'শত্য সংগ্রহ — জুলাই গণঅভ্যুত্থানের দাবি যাচাইকরণ | জুলাই হ্যাকাথন ২০২৬'
          : 'Shotto Songroho — Fact-Verification for July Revolution Claims | July Hackathon 2026'
        }
      </footer>
    </div>
  );
}
