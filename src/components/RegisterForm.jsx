import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './RegisterForm.css';

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    gender: '',
    height_cm: '',
    weight_kg: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [passwordStrength, setPasswordStrength] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

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
    if (!formData.email) e.email = 'Vui lòng nhập email';
    else if (!/^\S+@\S+\.\S+$/.test(formData.email)) e.email = 'Email không hợp lệ';
    
    if (!formData.password) {
      e.password = 'Vui lòng nhập mật khẩu';
    } else {
      const requirements = validatePassword(formData.password);
      if (requirements.length > 0) {
        e.password = requirements.join(', ');
      }
    }
    
    if (formData.password !== formData.confirmPassword) {
      e.confirmPassword = 'Mật khẩu không khớp';
    }

    if (!formData.firstName) e.firstName = 'Vui lòng nhập họ';
    if (!formData.lastName) e.lastName = 'Vui lòng nhập tên';

    return e;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Cập nhật strength indicator khi người dùng nhập mật khẩu
    if (name === 'password') {
      setPasswordStrength(checkPasswordStrength(value));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      setLoading(true);
      try {
        const userData = {
          email: formData.email,
          password: formData.password,
          confirm_password: formData.confirmPassword,
          first_name: formData.firstName,
          last_name: formData.lastName,
          gender: formData.gender || null,
          height_cm: formData.height_cm ? parseFloat(formData.height_cm) : null,
          weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : null
        };

        const result = await register(userData);
        if (result.success) {
          setSuccessMessage('Đăng ký thành công! Chuyển hướng đến trang đăng nhập...');
          setTimeout(() => {
            navigate('/login');
          }, 2000);
        } else {
          setErrors({ form: result.error });
        }
      } catch (error) {
        setErrors({ form: 'Có lỗi xảy ra khi đăng ký. Vui lòng thử lại.' });
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="register-page">
      <form className="register-card" onSubmit={handleSubmit} noValidate>
        <h2 className="title">Đăng ký tài khoản</h2>
        
        {errors.form && <div className="form-error">{errors.form}</div>}
        {successMessage && <div className="form-success">{successMessage}</div>}

        <div className="form-row">
          <label className="field">
            <span className="label-text">Họ</span>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              className={errors.firstName ? 'invalid' : ''}
              placeholder="Nhập họ"
            />
            {errors.firstName && <span className="error-text">{errors.firstName}</span>}
          </label>

          <label className="field">
            <span className="label-text">Tên</span>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              className={errors.lastName ? 'invalid' : ''}
              placeholder="Nhập tên"
            />
            {errors.lastName && <span className="error-text">{errors.lastName}</span>}
          </label>
        </div>

        <label className="field">
          <span className="label-text">Email</span>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={errors.email ? 'invalid' : ''}
            placeholder="you@example.com"
          />
          {errors.email && <span className="error-text">{errors.email}</span>}
        </label>

        <label className="field">
          <span className="label-text">Mật khẩu</span>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={errors.password ? 'invalid' : ''}
            placeholder="Nhập mật khẩu mạnh"
          />
          {passwordStrength && (
            <div className={`password-strength strength-${passwordStrength}`}>
              Độ mạnh: <strong>{passwordStrength}</strong>
            </div>
          )}
          {errors.password && <span className="error-text">{errors.password}</span>}
          <div className="password-requirements">
            <p className="requirement-title">Yêu cầu mật khẩu:</p>
            <ul>
              <li className={formData.password && /^.{6,}$/.test(formData.password) ? 'met' : ''}>
                Ít nhất 6 ký tự
              </li>
              <li className={formData.password && /[A-Z]/.test(formData.password) ? 'met' : ''}>
                Ít nhất 1 chữ hoa (A-Z)
              </li>
              <li className={formData.password && /[a-z]/.test(formData.password) ? 'met' : ''}>
                Ít nhất 1 chữ thường (a-z)
              </li>
              <li className={formData.password && /\d/.test(formData.password) ? 'met' : ''}>
                Ít nhất 1 số (0-9)
              </li>
              <li className={formData.password && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(formData.password) ? 'met' : ''}>
                Ít nhất 1 ký tự đặc biệt (!@#$%...)
              </li>
            </ul>
          </div>
        </label>

        <label className="field">
          <span className="label-text">Xác nhận mật khẩu</span>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={errors.confirmPassword ? 'invalid' : ''}
            placeholder="Xác nhận mật khẩu"
          />
          {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
        </label>

        <div className="form-row">
          <label className="field">
            <span className="label-text">Giới tính</span>
            <select name="gender" value={formData.gender} onChange={handleChange}>
              <option value="" disabled>Chọn giới tính</option>
              <option value="nam">Nam</option>
              <option value="nu">Nữ</option>
              <option value="khac">Khác</option>
            </select>
          </label>
        </div>

        <div className="form-row">
          <label className="field">
            <span className="label-text">Chiều cao (cm)</span>
            <input
              type="number"
              name="height_cm"
              value={formData.height_cm}
              onChange={handleChange}
              min="0"
              step="0.1"
              placeholder="Ví dụ: 170"
            />
          </label>

          <label className="field">
            <span className="label-text">Cân nặng (kg)</span>
            <input
              type="number"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              min="0"
              step="0.1"
              placeholder="Ví dụ: 65"
            />
          </label>
        </div>

        <button type="submit" className="btn" disabled={loading || !!successMessage}>
          {loading ? 'Đang xử lý...' : 'Đăng ký'}
        </button>

        <div className="login-hint">
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </div>
      </form>
    </div>
  );
}