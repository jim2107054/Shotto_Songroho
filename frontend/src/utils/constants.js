/**
 * Shotto Songroho — Constants
 */

export const API_BASE = '/api';

export const VERDICT_CONFIG = {
  verified: {
    icon: '✅',
    color: 'var(--color-verified)',
    bgClass: 'verified',
  },
  disputed: {
    icon: '⚠️',
    color: 'var(--color-disputed)',
    bgClass: 'disputed',
  },
  false: {
    icon: '❌',
    color: 'var(--color-false)',
    bgClass: 'false',
  },
  unverifiable: {
    icon: '❓',
    color: 'var(--color-unverifiable)',
    bgClass: 'unverifiable',
  },
};

export const PIPELINE_STEPS = [
  { key: 'claim', label_key: 'step_claim', icon: '📝' },
  { key: 'evidence', label_key: 'step_evidence', icon: '🔍' },
  { key: 'crosscheck', label_key: 'step_crosscheck', icon: '⚖️' },
  { key: 'image', label_key: 'step_image', icon: '🖼️' },
  { key: 'verdict', label_key: 'step_verdict', icon: '⚡' },
];
