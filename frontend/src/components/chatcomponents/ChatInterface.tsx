import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../../types/Chat';
import { sendQueryToBackend } from '../../services/ChatService';
import styles from './ChatInterface.module.scss';


type ChatInterfaceProps = {
  url: string;
  suggestions: string[];
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  url,
  suggestions,
}) => {
  const [query, setQuery] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(true);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const handleSend = async (customQuery?: string) => {
    const finalQuery = customQuery ?? query;
    if (!finalQuery.trim()) return;

    const userMessage: Message = { sender: 'user', text: finalQuery };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setShowSuggestions(false);

    try {
      const data = await sendQueryToBackend({
        query: finalQuery,
        url: url,
        mode: 'default'
      });

      const aiMessage: Message = {
        sender: 'ai',
        text: data.response || 'Réponse vide.'
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Erreur lors de la requête:', error);
      setMessages(prev => [
        ...prev,
        { sender: 'ai', text: 'Erreur de communication avec le serveur.' }
      ]);
    } finally {
      setQuery('');
      setLoading(false);
    }
  };

  const handleSuggestionClick = (text: string) => {
    handleSend(text);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={`container`}>
      {showSuggestions && suggestions.length > 0 && (
        <div className={`alert alert-info ${styles.suggestionBox}`}>
          <strong>Suggestions :</strong>
          <div className="row mt-3">
            {suggestions.map((s, i) => (
              <div key={i} className="col-md-6 mb-2">
                <button
                  className="btn btn-outline-secondary btn-sm w-100"
                  onClick={() => handleSuggestionClick(s)}
                >
                  {s}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={`border rounded p-3 mb-3 ${styles.chatBox}`}>
        {messages.length === 0 && !loading && (
          <p className="text-muted text-center">Aucun message pour le moment.</p>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`mb-2 ${styles.message}`}>
            <span
              className={`badge me-2 ${
                msg.sender === 'user' ? 'bg-primary' : 'bg-success'
              }`}
            >
              {msg.sender === 'user' ? 'Vous' : 'IA'}
            </span>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className={`mb-2 ${styles.message}`}>
            <span className="badge bg-success me-2">IA</span>
            <span className="d-inline-flex align-items-center">
              <div className="spinner-border spinner-border-sm text-success me-2" role="status" />
              IA est en train de répondre...
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-group">
        <input
          type="text"
          className="form-control"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Posez votre question ici..."
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button className="btn btn-success" onClick={() => handleSend()}>
          Envoyer
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;