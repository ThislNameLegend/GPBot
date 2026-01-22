import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8081/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        onLogin(data.token);
        navigate('/');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка авторизации');
      }
    } catch (err) {
      setError('Не удалось подключиться к серверу');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2><i className="bi bi-box-arrow-in-right"></i> Вход в систему</h2>
      
      {error && (
        <div className="alert alert-error">
          <i className="bi bi-exclamation-triangle"></i> {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username"><i className="bi bi-person"></i> Имя пользователя</label>
          <input
            type="text"
            id="username"
            className="form-control"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Введите логин"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="password"><i className="bi bi-key"></i> Пароль</label>
          <input
            type="password"
            id="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Введите пароль"
            required
            disabled={loading}
          />
        </div>

        <button type="submit" className="btn" disabled={loading}>
          {loading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Вход...
            </>
          ) : (
            <>
              <i className="bi bi-box-arrow-in-right me-2"></i>
              Войти
            </>
          )}
        </button>
      </form>

      <div className="mt-4 text-center">
        <p className="text-muted">
          <small>
            <i className="bi bi-info-circle"></i> Тестовые учетные записи:<br />
            <strong>admin / admin123</strong> (администратор)<br />
            <strong>user / user123</strong> (пользователь)
          </small>
        </p>
      </div>

      <div className="mt-4 text-center">
        <p>
          Нет аккаунта? <a href="#" onClick={(e) => {
            e.preventDefault();
            setUsername('user');
            setPassword('user123');
          }} className="text-primary">
            Используйте тестовый аккаунт
          </a>
        </p>
      </div>
    </div>
  );
}

export default Login;
