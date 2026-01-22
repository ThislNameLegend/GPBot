misha, [22.01.2026 14:16]
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import './App.css';
import Login from './components/Login';
import TestList from './components/TestList';
import TestView from './components/TestView';
import TestResult from './components/TestResult';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      fetchUserInfo(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async (userToken) => {
    try {
      const response = await fetch('http://localhost:8081/auth/user', {
        headers: { 'Authorization': Bearer ${userToken} }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setToken(userToken);
      } else {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    fetchUserInfo(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="loading">
        <div></div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="container">
            <Link to="/" className="logo">
              <i className="bi bi-clipboard-data"></i> MassPoll
            </Link>
            <div className="nav-links">
              <Link to="/"><i className="bi bi-house"></i> Главная</Link>
              <Link to="/tests"><i className="bi bi-list-check"></i> Тесты</Link>
              {token ? (
                <>
                  <span><i className="bi bi-person"></i> {user?.username}</span>
                  <button onClick={handleLogout}><i className="bi bi-box-arrow-right"></i> Выйти</button>
                </>
              ) : (
                <Link to="/login"><i className="bi bi-box-arrow-in-right"></i> Войти</Link>
              )}
            </div>
          </div>
        </nav>

        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={token ? <Navigate to="/" /> : <Login onLogin={handleLogin} />} />
            <Route path="/tests" element={token ? <TestList token={token} /> : <Navigate to="/login" />} />
            <Route path="/test/:id" element={token ? <TestView token={token} /> : <Navigate to="/login" />} />
            <Route path="/result/:testId" element={token ? <TestResult token={token} /> : <Navigate to="/login" />} />
          </Routes>
        </div>

        <footer>
          <div className="container">
            <p><i className="bi bi-c-circle"></i> 2024 MassPoll | Платформа для тестирования и опросов</p>
            <p className="mt-2">
              <small>
                <i className="bi bi-github"></i> GitHub | 
                <i className="bi bi-telegram ms-2"></i> Telegram Bot | 
                <i className="bi bi-envelope ms-2"></i> Контакты
              </small>
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

misha, [22.01.2026 14:16]
function Home() {
  return (
    <div className="home">
      <div className="text-center mb-5">
        <h1 className="display-4 mb-3">Добро пожаловать в MassPoll</h1>
        <p className="lead">Современная платформа для создания и прохождения тестов и опросов</p>
      </div>
      
      <div className="features">
        <div className="feature-card">
          <div className="mb-3">
            <i className="bi bi-clipboard-check" style={{ fontSize: '3rem', color: '#667eea' }}></i>
          </div>
          <h3>📚 Создание тестов</h3>
          <p>Легко создавайте тесты с различными типами вопросов. Настраивайте время прохождения, количество попыток и критерии оценивания.</p>
        </div>
        
        <div className="feature-card">
          <div className="mb-3">
            <i className="bi bi-bar-chart" style={{ fontSize: '3rem', color: '#764ba2' }}></i>
          </div>
          <h3>📊 Аналитика результатов</h3>
          <p>Получайте детальные отчеты по каждому тесту. Анализируйте ответы пользователей, стройте графики и отслеживайте прогресс.</p>
        </div>
        
        <div className="feature-card">
          <div className="mb-3">
            <i className="bi bi-robot" style={{ fontSize: '3rem', color: '#f093fb' }}></i>
          </div>
          <h3>🤖 Telegram интеграция</h3>
          <p>Проходите тесты прямо в Telegram! Наш бот предоставляет тот же функционал, что и веб-версия, в удобном мессенджере.</p>
        </div>
      </div>

      <div className="mt-5 text-center">
        <h3 className="mb-3">Как это работает?</h3>
        <div className="row justify-content-center">
          <div className="col-md-8">
            <div className="d-flex justify-content-around flex-wrap">
              <div className="text-center m-3">
                <div className="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center" style={{ width: '60px', height: '60px' }}>
                  <i className="bi bi-1"></i>
                </div>
                <p className="mt-2">Зарегистрируйтесь</p>
              </div>
              <div className="text-center m-3">
                <div className="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center" style={{ width: '60px', height: '60px' }}>
                  <i className="bi bi-2"></i>
                </div>
                <p className="mt-2">Выберите тест</p>
              </div>
              <div className="text-center m-3">
                <div className="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center" style={{ width: '60px', height: '60px' }}>
                  <i className="bi bi-3"></i>
                </div>
                <p className="mt-2">Ответьте на вопросы</p>
              </div>
              <div className="text-center m-3">
                <div className="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center" style={{ width: '60px', height: '60px' }}>
                  <i className="bi bi-4"></i>
                </div>
                <p className="mt-2">Получите результат</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
