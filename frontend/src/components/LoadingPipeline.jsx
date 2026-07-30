import React from 'react';
import { PIPELINE_STEPS } from '../utils/constants';

export default function LoadingPipeline({ activeStep, t }) {
  return (
    <div className="pipeline-loading">
      <div className="pipeline-steps">
        {PIPELINE_STEPS.map((step, idx) => {
          let status = 'pending';
          if (idx < activeStep) status = 'completed';
          else if (idx === activeStep) status = 'active';

          return (
            <div key={step.key} className={`pipeline-step ${status}`}>
              <div className="step-indicator">
                {status === 'completed' ? '✓' : status === 'active' ? (
                  <span className="spinner"></span>
                ) : (
                  idx + 1
                )}
              </div>
              <div className="step-content">
                <h4>{step.icon} {t[step.label_key]}</h4>
                <p>
                  {status === 'completed' && (t.lang === 'bn' ? 'সম্পন্ন' : 'Completed')}
                  {status === 'active' && (t.lang === 'bn' ? 'চলছে...' : 'Processing...')}
                  {status === 'pending' && (t.lang === 'bn' ? 'অপেক্ষমাণ' : 'Waiting...')}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
