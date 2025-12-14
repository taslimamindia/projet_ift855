import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Login = () => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/admin/memory';

const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.removeItem('isAuthenticated');
    
    const adminPassword =
        (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_ADMIN_PASSWORD) ||
        (globalThis as any).process?.env?.REACT_APP_ADMIN_PASSWORD;

    if (password === adminPassword) {
        localStorage.setItem('isAuthenticated', 'true');
        navigate(from, { replace: true });
    } else {
        localStorage.removeItem('isAuthenticated');
        setError('Mot de passe incorrect');
    }
};

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-4">
          <div className="card shadow">
            <div className="card-body">
              <h3 className="card-title text-center mb-4">Administration</h3>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="password" className="form-label">Mot de passe</label>
                  <input
                    type="password"
                    className="form-control"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Entrez le mot de passe"
                  />
                </div>
                {error && <div className="alert alert-danger">{error}</div>}
                <button type="submit" className="btn btn-primary w-100">
                  Se connecter
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
