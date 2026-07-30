/**
 * Shotto Songroho — API Client
 */

import { API_BASE } from '../utils/constants';

/**
 * Verify a claim through the multi-agent pipeline.
 */
export async function verifyClaim({ text, imageBase64, url, lang }) {
  const body = {};
  if (text) body.text = text;
  if (imageBase64) body.image_base64 = imageBase64;
  if (url) body.url = url;
  body.lang = lang || 'en';

  const response = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Search/browse the corpus.
 */
export async function searchCorpus({ query, dateFrom, dateTo, location, verdictLabel, limit } = {}) {
  const params = new URLSearchParams();
  if (query) params.set('query', query);
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);
  if (location) params.set('location', location);
  if (verdictLabel) params.set('verdict_label', verdictLabel);
  if (limit) params.set('limit', String(limit));

  const response = await fetch(`${API_BASE}/corpus?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Health check.
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

/**
 * Fetch the accountability index.
 */
export async function accountabilityIndex({ dateFrom, dateTo, location } = {}) {
  const params = new URLSearchParams();
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);
  if (location) params.set('location', location);

  const response = await fetch(`${API_BASE}/accountability-index?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Verify the integrity chain.
 */
export async function verifyChain() {
  const response = await fetch(`${API_BASE}/chain/verify`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Generate a shareable verdict card PNG.
 */
export async function generateShareCard(result) {
  const response = await fetch(`${API_BASE}/share-card`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      verdict: result.verdict,
      confidence: result.confidence,
      summary: result.summary,
      sources: result.sources || [],
    }),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.blob();
}
