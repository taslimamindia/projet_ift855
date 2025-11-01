import React from 'react';
import styles from './Chat.module.scss';
import ChatInterface from '../../chatcomponents/ChatInterface';

const suggestions = [
  "Quels sont les projets en cours du gouvernement ?",
  "Quelles sont les statistiques de santé publique ?",
  "Quels sont les ministères disponibles ?",
  "Quelle est la politique énergétique actuelle ?"
];

const GovGnChat: React.FC = () => {
  return (
    <div className={`container ${styles.chatContainer}`}>
      <h2 className="text-center mt-4">💬 Chat sur les données du Gouvernement Guinéen</h2>
      <p className="text-muted text-center mb-4">
        Posez vos questions sur les politiques publiques, les statistiques officielles ou les services gouvernementaux.
      </p>

      <div className={styles.chatBox}>
        <ChatInterface url={""} suggestions={suggestions} />
      </div>
    </div>
  );
};

export default GovGnChat;