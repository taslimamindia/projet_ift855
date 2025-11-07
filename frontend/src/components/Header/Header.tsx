import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './Header.module.scss';

const GitHubIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.11.82-.26.82-.577 0-.285-.01-1.04-.015-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.334-1.757-1.334-1.757-1.09-.745.083-.73.083-.73 1.205.085 1.84 1.238 1.84 1.238 1.07 1.835 2.807 1.305 3.492.998.108-.776.418-1.305.76-1.605-2.665-.303-5.466-1.334-5.466-5.933 0-1.31.467-2.38 1.235-3.22-.123-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.02.005 2.045.138 3.003.404 2.29-1.552 3.296-1.23 3.296-1.23.655 1.653.243 2.873.12 3.176.77.84 1.233 1.91 1.233 3.22 0 4.61-2.804 5.625-5.476 5.92.43.37.823 1.102.823 2.222 0 1.605-.015 2.898-.015 3.293 0 .32.216.694.825.576C20.565 21.796 24 17.298 24 12c0-6.63-5.37-12-12-12z"/>
  </svg>
);

const LinkedInIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM0 8h5v16H0V8zm7.5 0h4.8v2.2h.07c.67-1.27 2.3-2.6 4.73-2.6C22.6 7.6 24 10 24 13.9V24h-5V14.9c0-2.2-.04-5-3.04-5-3.05 0-3.52 2.38-3.52 4.84V24h-5V8z"/>
  </svg>
);

const MailIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
  </svg>
);


const Header: React.FC = () => {
  return (
    <header>
      <nav className={`navbar navbar-expand-lg navbar-light bg-white shadow-sm sticky-top ${styles.navbar}`}>
        <div className="container-fluid">

          <Link to="/" className={`navbar-brand d-flex align-items-center ${styles.brand}`}>
            <img src={"/img/logo.png"} alt="Logo" className={styles.logo} />
          </Link>
          <NavItems />
        </div>
      </nav>
    </header>
  );
};


const NavItems: React.FC = () => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className={styles.menuButton}
        aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
        type="button"
      >
        <span className={`${styles.hamburger} ${open ? styles.open : ''}`} aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      <div className={`${styles.navItems} ${open ? styles.open : ''}`} role="menu">
        <a
          href="https://mamadou.kassatech.org"
          className={`${styles.githubLink} ${styles.centerDesktop} ${styles.mobileSiteLink}`}
          title="Voir mon site"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Voir mon site"
          role="menuitem"
          onClick={() => setOpen(false)}
        >
          <i className={`bi bi-globe ${styles.githubIcon}`} aria-hidden="true"></i>
          <span className={styles.githubLabel}>Voir mon site</span>
        </a>

        <a
          className={styles.iconLink}
          href="https://github.com/taslimamindia"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub"
          role="menuitem"
          onClick={() => setOpen(false)}
        >
          <GitHubIcon />
        </a>

        <a
          className={styles.iconLink}
          href="https://www.linkedin.com/in/mamadou-taslima-diallo-879b78189"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="LinkedIn"
          role="menuitem"
          onClick={() => setOpen(false)}
        >
          <LinkedInIcon />
        </a>

        <a className={styles.iconLink} href="mailto:mamadou.taslima.diallo@usherbrooke.ca" aria-label="Email" role="menuitem" onClick={() => setOpen(false)}>
          <MailIcon />
        </a>
      </div>
    </>
  );
};

export default Header;
