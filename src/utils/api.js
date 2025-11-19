import axios from 'axios';

// Use environment variable for API base URL, fallback to localhost
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const api = axios.create({
  baseURL,
  timeout: 15000, // Tăng từ 5000ms lên 15000ms để tránh timeout quá sớm
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - thêm token vào header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Thêm refresh token vào header nếu có
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      config.headers['refresh-token'] = refreshToken;
    }
    
    // DEBUG: Log URL để kiểm tra
    console.log('[API] Request:', {
      method: config.method.toUpperCase(),
      url: config.baseURL + config.url,
      hasToken: !!token
    });
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - xử lý refresh token
api.interceptors.response.use(
  (response) => {
    // Kiểm tra nếu có token mới trong response headers
    const newAccessToken = response.headers['new-access-token'];
    const newRefreshToken = response.headers['new-refresh-token'];
    
    if (newAccessToken && newRefreshToken) {
      localStorage.setItem('token', newAccessToken);
      localStorage.setItem('refreshToken', newRefreshToken);
    }
    
    console.log('[API] Response Success:', {
      status: response.status,
      url: response.config.url
    });
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Xử lý timeout error
    if (error.code === 'ECONNABORTED') {
      console.error('[API] Request timeout:', error.message);
      return Promise.reject({
        ...error,
        message: 'Request timeout - please try again'
      });
    }

    // Log error details
    console.error('[API] Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.response?.data?.detail || error.message
    });

    // Nếu không phải lỗi 401 hoặc đã thử refresh
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Nếu đang refresh token, thêm request vào queue
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        })
        .catch(err => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token');
      }

      console.log('[API] Attempting to refresh token');

      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken
      });

      const { access_token, refresh_token } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', refresh_token);

      // Cập nhật token cho request hiện tại và các request trong queue
      originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
      processQueue(null, access_token);

      console.log('[API] Token refreshed successfully');
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      console.error('[API] Token refresh failed, redirecting to login');
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// API endpoints
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  requestPasswordReset: (email) => api.post('/auth/request-password-reset', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { token, newPassword }),
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  logoutAll: (userId) => api.post('/auth/logout-all', { user_id: userId }),
};

export const calorieAPI = {
  getDailyLog: () => api.get('/calorie/daily'),
  addFood: (data) => api.post('/calorie/food', data),
  searchFoods: (query) => api.get(`/calorie/search?q=${query}`),
};

export const workoutAPI = {
  getPlans: () => api.get('/workout/plans'),
  getPlanDetails: (id) => api.get(`/workout/plans/${id}`),
  createPlan: (data) => api.post('/workout/plans', data),
};

export const paymentAPI = {
  getSubscriptions: () => api.get('/payment/subscriptions'),
  subscribe: (planId) => api.post('/payment/subscribe', { planId }),
  getInvoices: () => api.get('/payment/invoices'),
};

export default api;