import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import './styles/App.css';

function App() {
  return (
    <BrowserRouter>
      <nav className="navbar">
        <Link to="/" className="nav-link">Главная</Link>
        <Link to="/login" className="nav-link">Войти</Link>
        <Link to="/surveys" className="nav-link">Опросы</Link>
      </nav>
      
      <div className="container">
        <Routes>
          <Route path="/" element={<div><h1>Главная страница</h1><p>Добро пожаловать в систему опросов!</p></div>} />
          <Route path="/login" element={<div><h1>Вход</h1><button>Войти как тест</button></div>} />
          <Route path="/surveys" element={<div><h1>Список опросов</h1><p>Опрос 1, Опрос 2</p></div>} />
          <Route path="/survey/:id" element={<div><h1>Прохождение опроса</h1></div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
