import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  Envelope,
  GenderIntersex,
  Ruler,
  Barbell,
  FloppyDisk,
  CheckCircle,
} from "phosphor-react";
import "./UserProfile.css"; // File CSS sẽ tạo ở bước 2

// Dữ liệu giả lập (Giả sử đã fetch từ API)
const MOCK_USER_DATA = {
  user_id: 101,
  first_name: "Nguyễn",
  last_name: "Văn An",
  email: "nguyen.van.an@example.com",
  gender: "Nam",
  height_cm: 175.5,
  weight_kg: 70.2,
};

const UserProfile = () => {
  // State chứa dữ liệu form, khởi tạo bằng mock data
  const [formData, setFormData] = useState(MOCK_USER_DATA);
  
  // State quản lý trạng thái lưu
  const [saveStatus, setSaveStatus] = useState("idle"); // idle | saving | success

  // Xử lý khi người dùng thay đổi input
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  // Xử lý khi nhấn nút "Lưu"
  const handleSubmit = (e) => {
    e.preventDefault(); // Ngăn form submit
    setSaveStatus("saving");

    // --- MÔ PHỎNG API CALL ĐỂ LƯU DATA ---
    console.log("Đang gửi dữ liệu cập nhật:", formData);
    setTimeout(() => {
      setSaveStatus("success");
      console.log("Cập nhật thành công!");

      // Tự động quay về trạng thái 'idle' sau 2 giây
      setTimeout(() => setSaveStatus("idle"), 2000);
    }, 1500); // Giả lập 1.5 giây
  };

  return (
    <motion.div
      className="profile-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="profile-wrapper">
        <h1 className="profile-title">Thông Tin Cá Nhân</h1>
        <p className="profile-subtitle">
          Cập nhật thông tin và các chỉ số cơ thể của bạn.
        </p>

        <form className="profile-form" onSubmit={handleSubmit}>
          {/* Hàng 1: Tên và Họ */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name" className="form-label">
                <User size={18} /> Tên
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                className="form-input"
                value={formData.first_name}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="last_name" className="form-label">
                <User size={18} /> Họ
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                className="form-input"
                value={formData.last_name}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Hàng 2: Email */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              <Envelope size={18} /> Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              className="form-input"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          {/* Hàng 3: Giới tính */}
          <div className="form-group">
            <label htmlFor="gender" className="form-label">
              <GenderIntersex size={18} /> Giới tính
            </label>
            <select
              id="gender"
              name="gender"
              className="form-select"
              value={formData.gender}
              onChange={handleChange}
            >
              <option value="Nam">Nam</option>
              <option value="Nữ">Nữ</option>
              <option value="Khác">Khác</option>
            </select>
          </div>

          {/* Hàng 4: Chiều cao và Cân nặng */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="height_cm" className="form-label">
                <Ruler size={18} /> Chiều cao (cm)
              </label>
              <input
                type="number"
                id="height_cm"
                name="height_cm"
                className="form-input"
                value={formData.height_cm}
                onChange={handleChange}
                step="0.1"
              />
            </div>
            <div className="form-group">
              <label htmlFor="weight_kg" className="form-label">
                <Barbell size={18} /> Cân nặng (kg)
              </label>
              <input
                type="number"
                id="weight_kg"
                name="weight_kg"
                className="form-input"
                value={formData.weight_kg}
                onChange={handleChange}
                step="0.1"
              />
            </div>
          </div>

          {/* Nút Lưu */}
          <div className="form-action-area">
            <button
              type="submit"
              className="save-button"
              disabled={saveStatus === "saving"}
            >
              <AnimatePresence mode="wait">
                {saveStatus === "saving" ? (
                  <motion.span
                    key="saving"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="button-text"
                  >
                    Đang lưu...
                  </motion.span>
                ) : saveStatus === "success" ? (
                  <motion.span
                    key="success"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="button-text"
                  >
                    <CheckCircle size={20} weight="bold" /> Đã lưu!
                  </motion.span>
                ) : (
                  <motion.span
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="button-text"
                  >
                    <FloppyDisk size={20} weight="bold" /> Lưu thay đổi
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
};

export default UserProfile;