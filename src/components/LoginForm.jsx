import "./LoginForm.css";
import React, { useState } from 'react';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

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

    // Mô phỏng gửi request
    try {
      setLoading(true);
      // TODO: Thay bằng call API thực tế
      await new Promise((r) => setTimeout(r, 800));
      
      // Call onLogin with credentials when login is successful
      onLogin({ email, password });
      
    } catch (err) {
      setErrors({ form: 'Lỗi khi đăng nhập. Thử lại.' });
    } finally {
      setLoading(false);
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

          <a className="forgot" href="#">Quên mật khẩu?</a>
        </div>

        <button className="btn" type="submit" disabled={loading}>
          {loading ? 'Đang xử lý...' : 'Đăng nhập'}
        </button>

        <div className="signup-hint">
          Chưa có tài khoản? <a href="#">Đăng ký</a>
        </div>
      </form>

    </div>
  );
}