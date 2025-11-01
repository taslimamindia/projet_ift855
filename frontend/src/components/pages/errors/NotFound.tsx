import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Errors.module.scss';

const NotFound: React.FC = () => {
  return (
    <div className={`container text-center ${styles.notFoundContainer}`}>
      <h1 className="display-4">404 - Page introuvable</h1>
      <p className="lead mb-4">
        Oups ! La page que vous cherchez n'existe pas ou a été déplacée.
      </p>
      <Link to="/" className="btn btn-primary">
        Retour à l'accueil
      </Link>
    </div>
  );
};

export default NotFound;