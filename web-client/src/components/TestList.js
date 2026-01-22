import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function TestList({ token }) {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTests();
  }, [token]);

  const fetchTests = async () => {
    try {
      const response = await fetch('http://localhost:8080/api/tests', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTests(data);
      } else if (response.status === 401) {
        setError('Требуется авторизация');
      } else {
        setError('Не удалось загрузить тесты');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
      console.error('Fetch tests error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div></div>
        <p className="mt-3">Загрузка тестов...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <i className="bi bi-exclamation-triangle"></i> {error}
        <button className="btn btn-sm btn-outline-primary ms-3" onClick={fetchTests}>
          <i className="bi bi-arrow-clockwise"></i> Повторить
        </button>
      </div>
    );
  }

  if (tests.length === 0) {
    return (
      <div className="text-center py-5">
        <i className="bi bi-clipboard-x" style={{ fontSize: '4rem', color: '#ccc' }}></i>
        <h3 className="mt-3">Тесты не найдены</h3>
        <p className="text-muted">Пока нет доступных тестов. Попробуйте позже.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2><i className="bi bi-list-check"></i> Доступные тесты</h2>
        <button className="btn btn-sm btn-outline-primary" onClick={fetchTests}>
          <i className="bi bi-arrow-clockwise"></i> Обновить
        </button>
      </div>

      <div className="test-list">
        {tests.map((test) => (
          <div key={test.id} className="test-card">
            <div className="d-flex justify-content-between align-items-start">
              <div>
                <h3 className="mb-2">{test.title}</h3>
                {test.description && (
                  <p className="text-muted mb-3">{test.description}</p>
                )}
              </div>
              <span className="badge bg-primary">
                <i className="bi bi-question-circle"></i> {test.questions_count || 0}
              </span>
            </div>
            
            <div className="test-meta mb-3">
              <span><i className="bi bi-clock"></i> {test.duration_minutes || 30} мин</span>
              <span><i className="bi bi-person"></i> Автор: Система</span>
            </div>

            <div className="d-grid">
              <Link to={`/test/${test.id}`} className="btn btn-primary">
                <i className="bi bi-play-circle"></i> Начать тест
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 alert alert-success">
        <i className="bi bi-info-circle"></i> Выберите тест и начните прохождение. 
        Результаты будут сохранены в вашем профиле.
      </div>
    </div>
  );
}

export default TestList;
