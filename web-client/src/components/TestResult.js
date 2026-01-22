import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';

function TestResult({ token }) {
  const { testId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState(location.state?.result);
  const [test, setTest] = useState(location.state?.test);
  const [answers, setAnswers] = useState(location.state?.answers);
  const [loading, setLoading] = useState(!location.state?.result);

  useEffect(() => {
    if (!location.state?.result) {
      fetchResult();
    }
  }, []);

  const fetchResult = async () => {
    try {
      const response = await fetch(`http://localhost:8080/api/tests/${testId}/results`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Fetch result error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div></div>
        <p className="mt-3">Загрузка результатов...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="alert alert-error">
        <i className="bi bi-exclamation-triangle"></i> Результаты не найдены
        <button className="btn btn-sm btn-outline-primary ms-3" onClick={() => navigate('/tests')}>
          <i className="bi bi-arrow-left"></i> Назад к тестам
        </button>
      </div>
    );
  }

  const scorePercentage = result.score || 0;
  const isPassed = scorePercentage >= 70;
  const totalQuestions = result.total_questions || 0;
  const correctAnswers = result.correct_answers || 0;

  return (
    <div className="result-container">
      <div className="score-circle">
        {scorePercentage}%
      </div>

      <h2 className="mb-3">
        {isPassed ? (
          <>
            <i className="bi bi-trophy-fill text-success me-2"></i>
            Тест пройден успешно!
          </>
        ) : (
          <>
            <i className="bi bi-emoji-frown text-warning me-2"></i>
            Тест не пройден
          </>
        )}
      </h2>

      <p className="lead mb-4">
        {test?.title || 'Результаты теста'}
      </p>

      <div className="result-details">
        <div className="detail-item">
          <span><i className="bi bi-check-circle text-success me-2"></i> Правильные ответы</span>
          <strong>{correctAnswers} из {totalQuestions}</strong>
        </div>
        
        <div className="detail-item">
          <span><i className="bi bi-x-circle text-danger me-2"></i> Неправильные ответы</span>
          <strong>{totalQuestions - correctAnswers}</strong>
        </div>
        
        <div className="detail-item">
          <span><i className="bi bi-percent text-primary me-2"></i> Результат</span>
          <strong>{scorePercentage}%</strong>
        </div>
        
        <div className="detail-item">
          <span><i className="bi bi-flag text-info me-2"></i> Статус</span>
          <strong className={isPassed ? 'text-success' : 'text-danger'}>
            {isPassed ? 'СДАНО' : 'НЕ СДАНО'}
          </strong>
        </div>
      </div>

      <div className="mt-5">
        <h4 className="mb-3">Детали по вопросам</h4>
        {test?.questions?.map((question, index) => (
          <div key={index} className="card mb-3">
            <div className="card-body">
              <h6 className="card-title">
                Вопрос {index + 1}: {question.text}
              </h6>
              <div className="mt-2">
                <strong>Ваш ответ:</strong>{' '}
                {answers && answers[index] !== -1 && question.options?.[answers[index]] 
                  ? question.options[answers[index]] 
                  : 'Нет ответа'}
              </div>
              {question.correct_answer !== undefined && (
                <div>
                  <strong>Правильный ответ:</strong>{' '}
                  {question.options?.[question.correct_answer] || 'Не указан'}
                </div>
              )}
              {answers && answers[index] === question.correct_answer ? (
                <div className="text-success mt-2">
                  <i className="bi bi-check-circle"></i> Правильно
                </div>
              ) : answers && answers[index] !== -1 ? (
                <div className="text-danger mt-2">
                  <i className="bi bi-x-circle"></i> Неправильно
                </div>
              ) : (
                <div className="text-warning mt-2">
                  <i className="bi bi-question-circle"></i> Пропущен
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 d-flex justify-content-center gap-3">
        <Link to="/tests" className="btn btn-primary">
          <i className="bi bi-list-check me-2"></i> К списку тестов
        </Link>
        <button className="btn btn-outline-secondary" onClick={() => navigate('/')}>
          <i className="bi bi-house me-2"></i> На главную
        </button>
      </div>

      <div className="mt-4 alert alert-info">
        <i className="bi bi-info-circle"></i> Результаты сохранены в вашем профиле. 
        Вы можете просмотреть их в любое время.
      </div>
    </div>
  );
}

export default TestResult;
