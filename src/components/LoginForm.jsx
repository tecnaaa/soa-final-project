import "./LoginForm.css";
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  // States cho Modal Quên mật khẩu
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMessage, setForgotMessage] = useState('');
  const [forgotError, setForgotError] = useState('');
  
  const { login, requestPasswordReset } = useAuth();
  const navigate = useNavigate();

  function validate() {
    const e = {};
    if (!email) e.email = 'Vui lòng nhập email';
    else if (!/^\S+@\S+\.\S+$/.test(email)) e.email = 'Email không hợp lệ';
    if (!password) e.password = 'Vui lòng nhập mật khẩu';
    else if (password.length < 6) e.password = 'Mật khẩu ít nhất 6 ký tự';
    return e;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    const e = validate();
    setErrors(e);
    if (Object.keys(e).length) return;

    try {
      setLoading(true);
      const result = await login(email, password);
      
      if (result.success) {
        navigate('/dashboard');
      } else {
        setErrors({ form: result.error || 'Lỗi khi đăng nhập. Thử lại.' });
      }
    } catch (err) {
      setErrors({ form: 'Lỗi kết nối. Vui lòng thử lại.' });
    } finally {
      setLoading(false);
    }
  }

  const validateForgotEmail = () => {
    if (!forgotEmail) {
      setForgotError('Vui lòng nhập email');
      return false;
    } else if (!/^\S+@\S+\.\S+$/.test(forgotEmail)) {
      setForgotError('Email không hợp lệ');
      return false;
    }
    return true;
  };

  // --- LOGIC XỬ LÝ QUÊN MẬT KHẨU ĐÃ CẬP NHẬT ---
  async function handleForgotPassword(ev) {
    ev.preventDefault();
    setForgotError('');
    setForgotMessage('');

    if (!validateForgotEmail()) return;

    try {
      setForgotLoading(true);
      
      // Gọi API (AuthContext sẽ bắt lỗi 404/400 từ backend và trả về trong result.error)
      const result = await requestPasswordReset(forgotEmail);
      
      if (result.success) {
        // Thành công (Backend trả 200 OK)
        // Sử dụng message từ backend hoặc message mặc định
        const msg = result.data?.message || 'Link đặt lại mật khẩu đã được gửi vào email của bạn.';
        setForgotMessage(msg);
        setForgotEmail(''); // Xóa email để tránh gửi lại nhầm
        
        // Tự động đóng modal sau 5s
        setTimeout(() => {
          setShowForgotModal(false);
          setForgotMessage('');
        }, 5000);
      } else {
        // Thất bại (Backend trả 404 Not Found hoặc 400 Bad Request)
        // result.error chứa 'detail' từ Python:
        // - "Tài khoản không tồn tại..."
        // - "Hệ thống đã gửi link... vẫn còn hiệu lực..."
        setForgotError(result.error || 'Có lỗi xảy ra. Vui lòng thử lại.');
      }
    } catch (err) {
      setForgotError('Lỗi hệ thống không mong muốn.');
    } finally {
      setForgotLoading(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit} noValidate>
        <h2 className="title">Đăng nhập</h2>

        {errors.form && <div className="form-error">{errors.form}</div>}

        <label className="field">
          <span className="label-text">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={`input ${errors.email ? 'invalid' : ''}`}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? 'email-error' : undefined}
          />
          {errors.email && (
            <small id="email-error" className="error-text">
              {errors.email}
            </small>
          )}
        </label>

        <label className="field">
          <span className="label-text">Mật khẩu</span>
          <div className="password-row">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Nhập mật khẩu"
              className={`input ${errors.password ? 'invalid' : ''}`}
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            <button
              type="button"
              className="show-btn"
              onClick={() => setShowPassword((s) => !s)}
              aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
            >
              {showPassword ? 'Ẩn' : 'Hiện'}
            </button>
          </div>
          {errors.password && (
            <small id="password-error" className="error-text">
              {errors.password}
            </small>
          )}
        </label>

        <div className="row-between">
          <label className="checkbox-wrap">
            <input type="checkbox" /> <span>Ghi nhớ tôi</span>
          </label>

          <button
            type="button"
            className="forgot"
            onClick={() => setShowForgotModal(true)}
          >
            Quên mật khẩu?
          </button>
        </div>

        <button className="btn" type="submit" disabled={loading}>
          {loading ? 'Đang xử lý...' : 'Đăng nhập'}
        </button>

        <div className="signup-hint">
          Chưa có tài khoản? <Link to="/register">Đăng ký</Link>
        </div>
      </form>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="modal-overlay" onClick={() => setShowForgotModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="close-btn"
              onClick={() => setShowForgotModal(false)}
              aria-label="Đóng modal"
            >
              ×
            </button>

            <h3 className="modal-title">Quên mật khẩu</h3>
            <p className="modal-description">
              Nhập email của bạn để nhận hướng dẫn đặt lại mật khẩu.
            </p>

            {forgotError && (
              <div className="form-error">{forgotError}</div>
            )}

            {forgotMessage && (
              <div className="form-success">{forgotMessage}</div>
            )}

            <form onSubmit={handleForgotPassword} noValidate>
              <label className="field">
                <span className="label-text">Email</span>
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="Nhập email của bạn"
                  className="input"
                  disabled={forgotLoading}
                />
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowForgotModal(false)}
                  disabled={forgotLoading}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="btn"
                  disabled={forgotLoading}
                >
                  {forgotLoading ? 'Đang gửi...' : 'Gửi yêu cầu'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}