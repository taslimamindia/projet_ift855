import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Home.module.scss';

const Home: React.FC = () => {
  const [url, setUrl] = useState('');
  const navigate = useNavigate();

  const handleGovClick = () => {
    navigate('/chat/gov/gn');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      navigate(`/chat/custom?url=${encodeURIComponent(url)}`);
    }
  };

  return (
    <div className={`container ${styles.homeContainer}`}>
      <h1 className="text-center mt-5">Bienvenue sur le Chat Data Explorer</h1>
      <p className="lead text-center mb-5">
        Choisissez une source de données pour démarrer votre session de chat.
      </p>

      <div className="row justify-content-center">
        <div className="col-md-6 mb-4">
          <div className={`card shadow-sm h-100 ${styles.card}`}>
            <div className="card-body text-center">
              <h5 className={styles.cardTitle}>📊 Site du gouvernement de la Guinée</h5>
              <p className={styles.cardText}>
                Utilisez ce modèle pour explorer les données officielles de la Guinée.
              </p>
              
            </div>
            <div className='card-footer text-center'>
              <button className="btn btn-primary" onClick={handleGovClick}>
                Démarrer le Chat
              </button>
            </div>
          </div>
        </div>

        <div className="col-md-6 mb-4">
          <form onSubmit={handleSubmit}>
            <div className={`card shadow-sm h-100 ${styles.card}`}>
              <div className="card-body text-center">
                <h5 className={styles.cardTitle}>🌐 Fournir une URL</h5>
                <p className={styles.cardText}>
                  Entrez l’adresse d’un site web pour crawler ses données et discuter avec l'AI.
                </p>
                
                  <input
                    id="url"
                    type="url"
                    placeholder="https://"
                    className="form-control mb-3"
                    value={url}
                    onChange={(e) => {
                      let value = e.target.value;
                      if (!value.startsWith("https://")) {
                        value = "https://";
                      }
                      setUrl(value);
                    }}
                    required
                  />                
              </div>
              <div className='card-footer text-center'>
                <button type="submit" className="btn btn-primary">
                    Lancer le Chat
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <div className={styles.diagramContainer}>
        <img
          src="/img/diagrammeRAG.jpg"
          alt="Diagramme RAG"
          className={styles.diagramImage}
        />
      </div>
    </div>
  );
};

export default Home;