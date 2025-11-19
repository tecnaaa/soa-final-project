import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tokens, setTokens] = useState(() => ({
    accessToken: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refreshToken')
  }));

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          // Gọi API lấy thông tin user ngay khi khởi động
          // Đảm bảo rằng api.getProfile() sử dụng token từ localStorage
          const response = await authAPI.getProfile();
          setUser(response.data);
        } catch (error) {
          console.error('Failed to fetch user profile on init:', error);
          // Nếu token hết hạn hoặc không hợp lệ, tự động logout
          if (error.response?.status === 401) {
            logout();
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []); // Chạy 1 lần khi mount

  const handleNewTokens = (accessToken, refreshToken) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
    setTokens({ accessToken, refreshToken });
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({
        username: email,
        password: password,
      });

      const { access_token, refresh_token, user: userData } = response.data;
      
      if (!access_token || !refresh_token) {
        throw new Error('Invalid response: missing tokens');
      }
      
      handleNewTokens(access_token, refresh_token);
      setUser(userData);
      setLoading(false);

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      return {
        success: false,
        error: error.response?.data?.detail || 'Lỗi khi đăng nhập'
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Lỗi khi đăng ký'
      };
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      const response = await authAPI.requestPasswordReset(email);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Password reset request error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Không thể gửi yêu cầu đặt lại mật khẩu. Vui lòng kiểm tra email và thử lại.'
      };
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      const response = await authAPI.resetPassword(token, newPassword);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Password reset error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Không thể đặt lại mật khẩu. Link có thể đã hết hạn. Vui lòng thử lại.'
      };
    }
  };

  const logout = (allDevices = false) => {
    if (allDevices && user) {
      authAPI.logoutAll({ user_id: user.id })
        .catch(error => console.error('Error logging out all devices:', error));
    }

    setUser(null);
    setTokens({ accessToken: null, refreshToken: null });
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  };

  const refreshAccessToken = async () => {
    try {
      const response = await authAPI.refresh(tokens.refreshToken);

      const { access_token, refresh_token } = response.data;
      handleNewTokens(access_token, refresh_token);
      return access_token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      logout();
      throw error;
    }
  };

  const updateProfile = (profileData) => {
    // Cập nhật user state trực tiếp (dùng cho khi server trả về user data sau upload/update)
    // Hoặc gọi API nếu chỉ truyền dữ liệu cần cập nhật
    if (profileData && profileData.user_id) {
      // Nếu là object user từ server, cập nhật trực tiếp
      setUser(profileData);
      return { success: true, data: profileData };
    } else {
      // Nếu là dữ liệu cần update, gọi API
      return updateProfileViaAPI(profileData);
    }
  };

  const updateProfileViaAPI = async (profileData) => {
    try {
      const response = await authAPI.updateProfile(profileData);
      setUser(response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating profile:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Lỗi khi cập nhật thông tin'
      };
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    register,
    requestPasswordReset,
    resetPassword,
    updateProfile,
    refreshAccessToken,
    tokens
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};