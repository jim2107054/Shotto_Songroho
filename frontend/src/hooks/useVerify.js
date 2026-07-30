/**
 * Shotto Songroho — useVerify Hook
 * Manages verification state and API calls.
 */

import { useState, useCallback } from 'react';
import { verifyClaim } from '../api/client';

export function useVerify() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeStep, setActiveStep] = useState(-1);

  const verify = useCallback(async ({ text, imageBase64, url, lang }) => {
    setLoading(true);
    setResult(null);
    setError(null);
    setActiveStep(0);

    // Simulate pipeline steps progressing
    const stepTimers = [];
    for (let i = 1; i <= 4; i++) {
      stepTimers.push(
        setTimeout(() => setActiveStep(i), i * 1200)
      );
    }

    try {
      const data = await verifyClaim({ text, imageBase64, url, lang });
      setResult(data);
      setActiveStep(5); // all done
    } catch (err) {
      setError(err.message || 'Verification failed');
      setActiveStep(-1);
    } finally {
      setLoading(false);
      stepTimers.forEach(clearTimeout);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setActiveStep(-1);
  }, []);

  return { loading, result, error, activeStep, verify, reset };
}
