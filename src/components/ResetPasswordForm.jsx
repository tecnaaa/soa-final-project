import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LoginForm.css';

export default function ResetPasswordForm() {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [passwordStrength, setPasswordStrength] = useState('');
  const { resetPassword } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const resetToken = searchParams.get('token');

  // Kiểm tra độ mạnh mật khẩu
  const checkPasswordStrength = (password) => {
    if (!password) return '';
    
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
    const isLongEnough = password.length >= 6;

    const strength = [hasUpperCase, hasLowerCase, hasNumber, hasSpecialChar, isLongEnough].filter(Boolean).length;

    if (strength < 2) return 'yếu';
    if (strength < 4) return 'trung bình';
    return 'mạnh';
  };

  const validatePassword = (pwd) => {
    const hasUpperCase = /[A-Z]/.test(pwd);
    const hasLowerCase = /[a-z]/.test(pwd);
    const hasNumber = /\d/.test(pwd);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd);
    const isLongEnough = pwd.length >= 6;

    const requirements = [];
    if (!isLongEnough) requirements.push('Ít nhất 6 ký tự');
    if (!hasUpperCase) requirements.push('Ít nhất 1 chữ hoa');
    if (!hasLowerCase) requirements.push('Ít nhất 1 chữ thường');
    if (!hasNumber) requirements.push('Ít nhất 1 số');
    if (!hasSpecialChar) requirements.push('Ít nhất 1 ký tự đặc biệt (!@#$%...)');

    return requirements;
  };

  const validate = () => {
    const e = {};
    
    if (!newPassword) {
      e.newPassword = 'Vui lòng nhập mật khẩu mới';
    } else {
      const requirements = validatePassword(newPassword);
      if (requirements.length > 0) {
        e.newPassword = requirements.join(', ');
      }
    }
    
    if (newPassword !== confirmPassword) {
      e.confirmPassword = 'Mật khẩu không khớp';
    }
    
    if (!resetToken) {
      e.token = 'Link đặt lại mật khẩu không hợp lệ';
    }
    
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      setLoading(true);
      try {
        const result = await resetPassword(resetToken, newPassword);
        
        if (result.success) {
          setSuccessMessage('Mật khẩu đã được đặt lại thành công! Chuyển hướng đến trang đăng nhập...');
          setTimeout(() => {
            navigate('/login');
          }, 2000);
        } else {
          setErrors({ form: result.error || 'Có lỗi xảy ra. Vui lòng thử lại.' });
        }
      } catch (error) {
        setErrors({ form: 'Có lỗi xảy ra. Vui lòng thử lại.' });
      } finally {
        setLoading(false);
      }
    }
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setNewPassword(value);
    setPasswordStrength(checkPasswordStrength(value));
  };

  if (!resetToken) {
    return (
      <div className="login-page">
        <div className="login-card">
          <h2 className="title">Đặt lại mật khẩu</h2>
          <div className="form-error">
            Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn
          </div>
          <button 
            className="btn"
            onClick={() => navigate('/login')}
            style={{ marginTop: '20px' }}
          >
            Quay lại trang đăng nhập
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit} noValidate>
        <h2 className="title">Đặt lại mật khẩu</h2>

        {errors.form && <div className="form-error">{errors.form}</div>}
        {successMessage && <div className="form-success">{successMessage}</div>}

        <label className="field">
          <span className="label-text">Mật khẩu mới</span>
          <div className="password-row">
            <input
              type={showPassword ? 'text' : 'password'}
              value={newPassword}
              onChange={handlePasswordChange}
              placeholder="Nhập mật khẩu mới"
              className={`input ${errors.newPassword ? 'invalid' : ''}`}
              disabled={loading || !!successMessage}
              aria-invalid={!!errors.newPassword}
              aria-describedby={errors.newPassword ? 'password-error' : undefined}
            />
            <button
              type="button"
              className="show-btn"
              onClick={() => setShowPassword((s) => !s)}
              disabled={loading || !!successMessage}
              aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
            >
              {showPassword ? 'Ẩn' : 'Hiện'}
            </button>
          </div>
          {passwordStrength && (
            <div className={`password-strength strength-${passwordStrength}`}>
              Độ mạnh: <strong>{passwordStrength}</strong>
            </div>
          )}
          {errors.newPassword && (
            <small id="password-error" className="error-text">
              {errors.newPassword}
            </small>
          )}
          <div className="password-requirements">
            <p className="requirement-title">Yêu cầu mật khẩu:</p>
            <ul>
              <li className={newPassword && /^.{6,}$/.test(newPassword) ? 'met' : ''}>
                Ít nhất 6 ký tự
              </li>
              <li className={newPassword && /[A-Z]/.test(newPassword) ? 'met' : ''}>
                Ít nhất 1 chữ hoa (A-Z)
              </li>
              <li className={newPassword && /[a-z]/.test(newPassword) ? 'met' : ''}>
                Ít nhất 1 chữ thường (a-z)
              </li>
              <li className={newPassword && /\d/.test(newPassword) ? 'met' : ''}>
                Ít nhất 1 số (0-9)
              </li>
              <li className={newPassword && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(newPassword) ? 'met' : ''}>
                Ít nhất 1 ký tự đặc biệt (!@#$%...)
              </li>
            </ul>
          </div>
        </label>

        <label className="field">
          <span className="label-text">Xác nhận mật khẩu</span>
          <div className="password-row">
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Xác nhận mật khẩu mới"
              className={`input ${errors.confirmPassword ? 'invalid' : ''}`}
              disabled={loading || !!successMessage}
              aria-invalid={!!errors.confirmPassword}
              aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
            />
            <button
              type="button"
              className="show-btn"
              onClick={() => setShowConfirmPassword((s) => !s)}
              disabled={loading || !!successMessage}
              aria-label={showConfirmPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
            >
              {showConfirmPassword ? 'Ẩn' : 'Hiện'}
            </button>
          </div>
          {errors.confirmPassword && (
            <small id="confirm-password-error" className="error-text">
              {errors.confirmPassword}
            </small>
          )}
        </label>

        <button 
          className="btn" 
          type="submit" 
          disabled={loading || !!successMessage}
          style={{ marginTop: '20px' }}
        >
          {loading ? 'Đang xử lý...' : 'Đặt lại mật khẩu'}
        </button>

        <div className="signup-hint">
          <a href="/login" style={{ textDecoration: 'none' }}>Quay lại trang đăng nhập</a>
        </div>
      </form>
    </div>
  );
}