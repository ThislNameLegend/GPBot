import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8080';
const AUTH_BASE = process.env.REACT_APP_AUTH_URL || 'http://localhost:8081';

const api = axios.create({
  baseURL: API_BASE,
});

const authApi = axios.create({
  baseURL: AUTH_BASE,
});

// Перехватчик для добавления токена
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username, password) => {
    const response = await authApi.post('/auth/login', { username, password });
    return response.data;
  },

  validateToken: async (token) => {
    const response = await authApi.get(`/auth/validate?token=${token}`);
    return response.data;
  },

  getUserInfo: async (token) => {
    const response = await authApi.get('/auth/user', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};

export const testService = {
  getTests: async () => {
    const response = await api.get('/api/tests');
    return response.data;
  },

  getTest: async (testId) => {
    const response = await api.get(`/api/tests/${testId}`);
    return response.data;
  },

  submitTest: async (testId, answers, userId) => {
    const response = await api.post(`/api/tests/${testId}/submit`, {
      answers,
      user_id: userId
    });
    return response.data;
  },

  getResults: async (testId) => {
    const response = await api.get(`/api/tests/${testId}/results`);
    return response.data;
  },

  createTest: async (title, description, questions) => {
    const response = await api.post('/api/tests', {
      title,
      description,
      questions
    });
    return response.data;
  }
};

export const healthService = {
  checkAuth: async () => {
    const response = await authApi.get('/health');
    return response.data;
  },

  checkCore: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

export default api;
