import React, { useState, useEffect } from 'react';
import './ConsentManager.css';

const ConsentManager = ({ tokenId }) => {
  const [consent, setConsent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConsent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokenId]);

  const fetchConsent = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_BASE}/api/consents/${tokenId}`
      );
      const data = await response.json();
      setConsent(data);
    } catch (error) {
      console.error('Consent fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const withdrawConsent = async () => {
    try {
      await fetch(
        `${process.env.REACT_APP_API_BASE}/api/consents/${tokenId}/withdraw`,
        {
          method: 'POST',
        }
      );
      await fetchConsent();
    } catch (error) {
      console.error('Withdraw consent error:', error);
    }
  };

  if (loading) {
    return (
      <div className="consent-loading">
        Cargando consentimiento...
      </div>
    );
  }

  return (
    <div className="consent-manager">
      <h3>Gestión de Consentimiento GDPR - Token {tokenId}</h3>
      {consent && (
        <div className={`consent-status ${consent.status}`}>
          <p>
            <strong>Estado:</strong> {consent.status.toUpperCase()}
          </p>
          <p>
            <strong>Fecha:</strong>{' '}
            {new Date(consent.timestamp).toLocaleString('es-ES')}
          </p>
          {consent.gaiachain_tx && (
            <p>
              <strong>GaiaChain TX:</strong> {consent.gaiachain_tx}
            </p>
          )}
          {consent.ipfs_cid && (
            <p>
              <strong>IPFS:</strong> {consent.ipfs_cid}
            </p>
          )}
          <button onClick={withdrawConsent} className="withdraw-btn">
            Retirar Consentimiento
          </button>
        </div>
      )}
    </div>
  );
};

export default ConsentManager;

