import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { usersAPI } from '../utils/apiServices';
import api from '../utils/api';
import './UserProfile.css';

export default function UserProfile() {
  const { user, logout, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  // State cho avatar
  const [avatarFile, setAvatarFile] = useState(null);
  // Mặc định dùng ảnh default nếu chưa có user
  const [previewUrl, setPreviewUrl] = useState("http://localhost:8001/files/default.webp");
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    password: '',
    confirm_password: ''
  });

  // Lấy Base URL (8001)
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

  // Hàm tạo URL avatar chuẩn (Đồng bộ logic với RightSidebar)
  const getAvatarUrl = (currentUser) => {
    if (!currentUser) return `${API_BASE_URL}/files/default.webp`;
    
    // 1. Ưu tiên avatar_url từ DB nếu có
    if (currentUser.avatar_url) {
        // Nếu avatar_url đã là full link (http...) thì dùng luôn
        if (currentUser.avatar_url.startsWith('http')) return currentUser.avatar_url;
        // Nếu là relative path (/files/...) thì ghép với BASE_URL
        return `${API_BASE_URL}${currentUser.avatar_url}`;
    }
    
    // 2. Nếu không, thử dùng convention theo user_id (giống RightSidebar)
    // RightSidebar dùng: http://localhost:8002/files/3.png
    // Ta dùng qua Gateway: http://localhost:8001/files/3.png
    if (currentUser.user_id) {
        return `${API_BASE_URL}/files/${currentUser.user_id}.png`;
    }

    // 3. Fallback cuối cùng
    return `${API_BASE_URL}/files/default.webp`;
  };

  // Cập nhật form và avatar khi user thay đổi
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        gender: user.gender || '',
        height_cm: user.height_cm || '',
        weight_kg: user.weight_kg || '',
        password: '',
        confirm_password: ''
      });
      
      // Cập nhật preview ảnh
      // Thêm tham số timestamp để tránh cache khi vừa upload xong
      const url = getAvatarUrl(user);
      setPreviewUrl(url);
    }
  }, [user]);

  // Xử lý chọn file ảnh
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        setError('Chỉ chấp nhận các file ảnh (jpg, png, gif, webp)');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setError('File quá lớn. Tối đa 5MB');
        return;
      }

      setAvatarFile(file);
      setPreviewUrl(URL.createObjectURL(file)); // Preview ảnh local ngay lập tức
      setError(null);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Upload avatar
  const uploadAvatar = async () => {
    if (!avatarFile) return true;

    setUploadingAvatar(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', avatarFile);
      
      // Gọi API upload
      const response = await api.post('/users/me/upload-profile-image', formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Backend trả về user mới hoặc url mới
      if (response.data) {
          // Cập nhật context user để toàn bộ app (kể cả RightSidebar) nhận ảnh mới
          // Nếu response trả về user object
          if (response.data.user_id) {
             updateProfile(response.data);
          } 
          // Nếu chỉ trả về url, ta tự merge (tùy backend trả về gì)
          else if (response.data.avatar_url) {
             updateProfile({ ...user, avatar_url: response.data.avatar_url });
          }
          
          // Force cập nhật lại preview với timestamp để tránh cache
          setPreviewUrl(`${API_BASE_URL}/files/${user.user_id}.png?t=${new Date().getTime()}`);
      }
      
      setAvatarFile(null);
      return true;
    } catch (err) {
      console.error("Upload error:", err);
      const errorMsg = err.response?.data?.detail || 'Lỗi khi tải ảnh lên';
      setError(errorMsg);
      setUploadingAvatar(false);
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      // 1. Upload Avatar trước
      if (avatarFile) {
        const uploadSuccess = await uploadAvatar();
        if (!uploadSuccess) {
          setLoading(false);
          return;
        }
      }

      // 2. Cập nhật thông tin text
      if (formData.password || formData.confirm_password) {
        if (formData.password !== formData.confirm_password) {
          throw new Error('Mật khẩu không khớp');
        }
      }

      const updateData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        gender: formData.gender === '' ? null : formData.gender, 
        height_cm: formData.height_cm ? parseFloat(formData.height_cm) : null,
        weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : null
      };

      if (formData.password) {
        updateData.password = formData.password;
      }

      const result = await usersAPI.updateProfile(updateData);
      
      // Cập nhật lại form
      setFormData({
        first_name: result.data.first_name || '',
        last_name: result.data.last_name || '',
        email: result.data.email || '',
        gender: result.data.gender || '',
        height_cm: result.data.height_cm || '',
        weight_kg: result.data.weight_kg || '',
        password: '',
        confirm_password: ''
      });

      setIsEditing(false);
      setSuccessMessage('Cập nhật thông tin thành công!');
      
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Có lỗi xảy ra');
    } finally {
      setLoading(false);
      setUploadingAvatar(false);
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>Hồ sơ cá nhân</h2>
        {error && <div className="error-message">{error}</div>}
        {successMessage && <div className="success-message">{successMessage}</div>}
        
        <form onSubmit={handleSubmit}>
          
          {/* Avatar Section */}
          <div className="profile-avatar-section" style={{textAlign: 'center', marginBottom: '2rem'}}>
            <div style={{width: '120px', height: '120px', margin: '0 auto', position: 'relative'}}>
                <img 
                    src={previewUrl} 
                    alt="Avatar" 
                    onError={(e) => {
                      // Chặn lặp vô hạn
                      if (e.target.src.includes('default.webp')) return;
                      // Fallback về ảnh mặc định qua Gateway (cổng 8001)
                      e.target.src = `${API_BASE_URL}/files/default.webp`;
                    }}
                    style={{
                        width: '100%', 
                        height: '100%', 
                        borderRadius: '50%', 
                        objectFit: 'cover', 
                        border: '3px solid #e5e7eb'
                    }}
                />
            </div>
            {isEditing && (
                <div style={{marginTop: '10px'}}>
                    <label htmlFor="avatar-upload" className="edit-button" style={{cursor: 'pointer', fontSize: '14px', padding: '5px 10px'}}>
                        {uploadingAvatar ? 'Đang tải...' : 'Đổi ảnh'}
                    </label>
                    <input 
                        id="avatar-upload" 
                        type="file" 
                        accept="image/*" 
                        onChange={handleFileChange}
                        disabled={uploadingAvatar}
                        style={{display: 'none'}} 
                    />
                </div>
            )}
          </div>

          {/* Form Fields - Giữ nguyên */}
          <div className="form-row">
            <div className="form-group">
              <label>Họ</label>
              <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} disabled={!isEditing} />
            </div>
            <div className="form-group">
              <label>Tên</label>
              <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} disabled={!isEditing} />
            </div>
          </div>

          <div className="form-group">
            <label>Email</label>
            <input type="email" value={formData.email} disabled={true} />
          </div>
          
          <div className="form-row">
             <div className="form-group">
              <label>Giới tính</label>
              <select name="gender" value={formData.gender} onChange={handleChange} disabled={!isEditing}>
                <option value="">Không chọn</option>
                <option value="nam">Nam</option>
                <option value="nu">Nữ</option>
                <option value="khac">Khác</option>
              </select>
            </div>
          </div>
          
          <div className="form-row">
             <div className="form-group">
               <label>Chiều cao (cm)</label>
               <input type="number" name="height_cm" value={formData.height_cm} onChange={handleChange} disabled={!isEditing} />
             </div>
             <div className="form-group">
               <label>Cân nặng (kg)</label>
               <input type="number" name="weight_kg" value={formData.weight_kg} onChange={handleChange} disabled={!isEditing} />
             </div>
          </div>

          {isEditing && (
            <div className="form-row">
              <div className="form-group">
                <label>Mật khẩu mới (tùy chọn)</label>
                <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="Để trống nếu không đổi" />
              </div>
              <div className="form-group">
                <label>Xác nhận mật khẩu</label>
                <input type="password" name="confirm_password" value={formData.confirm_password} onChange={handleChange} placeholder="Để trống nếu không đổi" />
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="button-group">
            {!isEditing ? (
              <button type="button" className="edit-button" onClick={() => setIsEditing(true)}>Chỉnh sửa</button>
            ) : (
              <>
                <button type="submit" className="save-button" disabled={loading || uploadingAvatar}>
                  {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
                </button>
                <button type="button" className="cancel-button" onClick={() => { setIsEditing(false); setAvatarFile(null); }} disabled={loading || uploadingAvatar}>
                  Hủy
                </button>
              </>
            )}
            <button type="button" className="logout-button" onClick={logout}>Đăng xuất</button>
          </div>
        </form>
      </div>
    </div>
  );
}