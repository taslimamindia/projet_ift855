import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Home.module.scss';

const Home: React.FC = () => {
  const [url, setUrl] = useState('');
  const [maxDepth, setMaxDepth] = useState<number>(250);
  const navigate = useNavigate();
  

  const handleGovClick = () => {
    navigate('/chat/gov/gn');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      const clamped = Math.max(50, Math.min(1000, Number(maxDepth) || 250));
      navigate(`/chat/custom?url=${encodeURIComponent(url)}&max_depth=${clamped}`);
    }
  };

  
  return (
    <div className={`container ${styles.homeContainer}`}>
      <h1 className="text-center mt-5">Bienvenue sur le Chat Data Explorer</h1>
      <p className={`lead text-center mb-5 ${styles.paragraph}`}>
        Choisissez une source de données pour démarrer votre session de chat.
      </p>

      <div className={`row justify-content-center ${styles.equalHeightRow}`}>
        <div id='comp1' className="col-md-6 mb-4">
          <div className={`card shadow-sm h-100 ${styles.card}`}>
            <div className="card-body text-center">
              <h5 className={styles.cardTitle}>📊 Site du gouvernement de la Guinée</h5>
              <p className={`${styles.cardText} ${styles.paragraph}`}>
                Utilisez ce modèle pour explorer les données officielles de la Guinée.
              </p>
            </div>
            <div className={styles.govImageWrapper}>
              <img
                src="/img/republique-de-guinee.jpg"
                alt="République de Guinée"
                className={styles.govImage}
              />
            </div>
            <div className='card-footer text-center'>
              <button className="btn btn-primary" onClick={handleGovClick}>
                Démarrer le Chat
              </button>
            </div>
          </div>
        </div>

        <div id='comp2' className="col-md-6 mb-4">
          <form className='h-100' onSubmit={handleSubmit}>
            <div className={`card shadow-sm h-100 ${styles.card}`}>
              <div className="card-body text-center">
                <h5 className={styles.cardTitle}>🌐 Fournir une URL</h5>
                <p className={`${styles.cardText} ${styles.paragraph}`}>
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
                <div className="mb-3 text-start">
                  <label htmlFor="maxDepth" className={`form-label ${styles.paragraph}`}>Nombre maximal de pages à crawler</label>
                  <input
                    id="maxDepth"
                    type="number"
                    className="form-control"
                    value={maxDepth}
                    min={50}
                    max={1000}
                    onChange={(e) => {
                      let v = Number(e.target.value);
                      if (Number.isNaN(v)) v = 250;
                      v = Math.max(50, Math.min(1000, Math.trunc(v)));
                      setMaxDepth(v);
                    }}
                    aria-describedby="maxDepthHelp"
                  />
                  <div id="maxDepthHelp" className={`form-text ${styles.paragraphSmall}`}>Intervalle autorisé : 50 à 1000 pages — valeur par défaut : 250</div>
                </div>

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

  <div className={styles.githubInlineWrapper}>
        <a
          href="https://github.com/taslimamindia/projet_ift855"
          className={`${styles.githubLink} ${styles.githubInline}`}
          title="Voir le dépôt du projet sur GitHub"
          target="_blank"
          rel="noopener noreferrer"
        >
          <svg
            className={styles.githubIcon}
            viewBox="0 0 16 16"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.5-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          <span className={styles.githubLabel}>Voir le projet</span>
        </a>
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