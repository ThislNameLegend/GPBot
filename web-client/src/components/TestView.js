import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function TestView({ token }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTest();
  }, [id, token]);

  const fetchTest = async () => {
    try {
      const response = await fetch(`http://localhost:8080/api/tests/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTest(data);
        setQuestions(data.questions || []);
        setAnswers(new Array(data.questions?.length || 0).fill(-1));
      } else {
        setError('Не удалось загрузить тест');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
      console.error('Fetch test error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (questionIndex, answerIndex) => {
    const newAnswers = [...answers];
    newAnswers[questionIndex] = answerIndex;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrev = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    if (window.confirm('Завершить тест и отправить ответы?')) {
      setSubmitting(true);
      try {
        const response = await fetch(`http://localhost:8080/api/tests/${id}/submit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            answers: answers.filter(a => a !== -1),
            user_id: 1 // В реальном приложении получать из токена
          })
        });

        if (response.ok) {
          const result = await response.json();
          navigate(`/result/${id}`, { state: { result, test, answers } });
        } else {
          setError('Ошибка при отправке ответов');
        }
      } catch (err) {
        setError('Ошибка подключения к серверу');
        console.error('Submit error:', err);
      } finally {
        setSubmitting(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div></div>
        <p className="mt-3">Загрузка теста...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <i className="bi bi-exclamation-triangle"></i> {error}
        <button className="btn btn-sm btn-outline-primary ms-3" onClick={() => navigate('/tests')}>
          <i className="bi bi-arrow-left"></i> Назад к списку
        </button>
      </div>
    );
  }

  if (!test || questions.length === 0) {
    return (
      <div className="alert alert-error">
        <i className="bi bi-exclamation-triangle"></i> Тест не найден или пуст
        <button className="btn btn-sm btn-outline-primary ms-3" onClick={() => navigate('/tests')}>
          <i className="bi bi-arrow-left"></i> Назад к списку
        </button>
      </div>
    );
  }

  const currentQ = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;
  const answeredCount = answers.filter(a => a !== -1).length;

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2><i className="bi bi-clipboard-check"></i> {test.title}</h2>
          {test.description && (
            <p className="text-muted mb-0">{test.description}</p>
          )}
        </div>
        <div className="text-end">
          <div className="badge bg-primary mb-1">
            Вопрос {currentQuestion + 1} из {questions.length}
          </div>
          <div className="text-muted small">
            Отвечено: {answeredCount}/{questions.length}
          </div>
        </div>
      </div>

      {/* Прогресс бар */}
      <div className="progress mb-4" style={{ height: '8px' }}>
        <div 
          className="progress-bar bg-success" 
          role="progressbar" 
          style={{ width: `${progress}%` }}
          aria-valuenow={progress} 
          aria-valuemin="0" 
          aria-valuemax="100"
        ></div>
      </div>

      {/* Вопрос */}
      <div className="question-container">
        <h4 className="question-text">
          <span className="badge bg-secondary me-2">{currentQuestion + 1}</span>
          {currentQ.text}
        </h4>

        <div className="options-list">
          {currentQ.options && currentQ.options.map((option, index) => (
            <div
              key={index}
              className={`option-item ${answers[currentQuestion] === index ? 'selected' : ''}`}
              onClick={() => handleAnswerSelect(currentQuestion, index)}
            >
              <div className="d-flex align-items-center">
                <div className="me-3">
                  <div className={`rounded-circle ${answers[currentQuestion] === index ? 'bg-primary text-white' : 'bg-light'} d-flex align-items-center justify-content-center`} style={{ width: '30px', height: '30px' }}>
                    {String.fromCharCode(65 + index)} {/* A, B, C, D */}
                  </div>
                </div>
                <div className="flex-grow-1">{option}</div>
                {answers[currentQuestion] === index && (
                  <div className="ms-2 text-primary">
                    <i className="bi bi-check-circle-fill"></i>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Навигация */}
      <div className="d-flex justify-content-between mt-4">
        <div>
          <button 
            className="btn btn-outline-secondary" 
            onClick={handlePrev}
            disabled={currentQuestion === 0}
          >
            <i className="bi bi-chevron-left"></i> Назад
          </button>
        </div>

        <div className="d-flex gap-2">
          {currentQuestion < questions.length - 1 ? (
            <button 
              className="btn btn-primary" 
              onClick={handleNext}
            >
              Далее <i className="bi bi-chevron-right"></i>
            </button>
          ) : (
            <button 
              className="btn btn-success" 
              onClick={handleSubmit}
              disabled={submitting || answeredCount === 0}
            >
              {submitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Отправка...
                </>
              ) : (
                <>
                  <i className="bi bi-check-circle me-2"></i>
                  Завершить тест
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Индикаторы вопросов */}
      <div className="mt-4">
        <h6 className="mb-2">Вопросы:</h6>
        <div className="d-flex flex-wrap gap-2">
          {questions.map((_, index) => (
            <button
              key={index}
              className={`btn btn-sm ${index === currentQuestion ? 'btn-primary' : answers[index] !== -1 ? 'btn-success' : 'btn-outline-secondary'}`}
              onClick={() => setCurrentQuestion(index)}
              style={{ width: '40px', height: '40px' }}
            >
              {index + 1}
            </button>
          ))}
        </div>
        <div className="mt-2 text-muted small">
          <span className="badge bg-success me-2">✓</span> Отвечено 
          <span className="badge bg-secondary mx-2">○</span> Не отвечено 
          <span className="badge bg-primary ms-2">●</span> Текущий
        </div>
      </div>

      {/* Предупреждение */}
      {answeredCount < questions.length && (
        <div className="alert alert-warning mt-4">
          <i className="bi bi-exclamation-triangle"></i> Вы ответили на {answeredCount} из {questions.length} вопросов. 
          Рекомендуется ответить на все вопросы перед завершением теста.
        </div>
      )}
    </div>
  );
}

export default TestView;
