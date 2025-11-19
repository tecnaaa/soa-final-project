/**
 * Organized API layer cho frontend
 * Tách biệt API calls theo service
 */

import api from './api';

// ============= USERS SERVICE =============
export const usersAPI = {
  getCurrentUser: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
  getUserStats: (userId) => api.get(`/users/${userId}/stats`),
  changePassword: (oldPassword, newPassword) =>
    api.post('/users/change-password', { oldPassword, newPassword }),
};

// ============= WORKOUT SERVICE =============
export const workoutAPI = {
  // Lấy danh sách kế hoạch của user
  getUserPlans: (userId) => api.get(`/workout/workout-plans/user/${userId}`),
  
  // Lấy chi tiết một kế hoạch
  getPlanDetails: (planId) => api.get(`/workout/workout-plans/${planId}`),
  
  // Tạo kế hoạch mới
  createPlan: (data) => api.post('/workout/workout-plans/', data),
  
  // Lấy danh sách bài tập (Exercise Library)
  // Hỗ trợ filters như: user_id, category_id, difficulty, etc.
  getExercises: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.category_id) params.append('category_id', filters.category_id);
    if (filters.muscle_group_id) params.append('muscle_group_id', filters.muscle_group_id);
    if (filters.difficulty) params.append('difficulty', filters.difficulty);
    if (filters.skip !== undefined) params.append('skip', filters.skip);
    if (filters.limit !== undefined) params.append('limit', filters.limit);
    
    const queryString = params.toString();
    const url = queryString ? `/workout/exercises/?${queryString}` : '/workout/exercises/';
    return api.get(url);
  },
  
  // Ghi nhận tiến độ tập luyện
  logProgress: (data) => api.post('/workout/progress/', data),
  
  // Lấy lịch sử tập luyện
  getProgressHistory: (userId) => api.get(`/workout/progress/user/${userId}`),
  
  // Lấy thống kê tiến độ
  getProgressStats: (userId) => api.get(`/workout/progress/stats/user/${userId}`),
};

// ============= NUTRITION SERVICE =============
export const nutritionAPI = {
  getMeals: (date = null) =>
    api.get('/nutrition/list', { params: { date } }),
  logMeal: (data) => api.post('/nutrition/log-meal', data),
  getMealPlan: (userId) => api.get(`/nutrition/plan/${userId}`),
  generateMealPlan: (preferences) =>
    api.post('/nutrition/generate-plan', preferences),
  deleteMeal: (mealId) => api.delete(`/nutrition/meal/${mealId}`),
};

// ============= CALORIES SERVICE =============
export const caloriesAPI = {
  getDailyCalories: (date = null) =>
    api.get('/calories/daily', { params: { date } }),
  getCalorieHistory: (startDate, endDate) =>
    api.get('/calories/history', { params: { startDate, endDate } }),
  calculateCalories: (activityData) =>
    api.post('/calories/calculate', activityData),
};

// ============= PAYMENT SERVICE =============
export const paymentAPI = {
  getPaymentHistory: () => api.get('/payment/history'),
  initiatePayment: (data) => api.post('/payment/initiate', data),
  processPayment: (data) => api.post('/payment/process', data),
  getSubscriptionStatus: () => api.get('/payment/subscription'),
  cancelSubscription: () => api.post('/payment/subscription/cancel'),
  updatePaymentMethod: (data) => api.put('/payment/method', data),
};

// ============= AUTH SERVICE =============
export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', { username: email, password }),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: (refreshToken) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
};

export default {
  usersAPI,
  workoutAPI,
  nutritionAPI,
  caloriesAPI,
  paymentAPI,
  authAPI,
};
