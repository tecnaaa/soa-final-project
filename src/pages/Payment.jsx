import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Crown, CheckCircle, XCircle, Prohibit } from "phosphor-react";
import "./Payment.css"; // File CSS chúng ta sẽ tạo ở bước 2

// --- DỮ LIỆU GIẢ LẬP (MOCK DATA) ---
// Dựa trên bảng 'subscriptions'
const MOCK_SUBSCRIPTIONS = [
  {
    subscription_id: 1,
    subscription_name: "Gói Premium",
    price: 150000,
    duration_days: 30,
    description: "Truy cập tất cả bài tập và kế hoạch dinh dưỡng.",
  },
  {
    subscription_id: 2,
    subscription_name: "Gói Coaching 1-1",
    price: 2500000,
    duration_days: 30,
    description: "Nhận hướng dẫn trực tiếp từ Huấn Luyện Viên.",
  },
];

// Dựa trên bảng 'user_subscriptions' (Giả sử user đang dùng gói Free)
const MOCK_CURRENT_USER_SUB = {
  user_subscription_id: null,
  subscription_id: null, // null = Gói Free
  subscription_name: "Gói Free",
  end_date: "Vĩnh viễn",
};

// --- COMPONENT ---
const Payment = () => {
  // State chứa gói hiện tại của user
  const [currentSub, setCurrentSub] = useState(MOCK_CURRENT_USER_SUB);
  
  // State chứa các gói có sẵn để mua
  const [packages, setPackages] = useState(MOCK_SUBSCRIPTIONS);
  
  // State theo dõi gói đang được chọn
  const [selectedPackageId, setSelectedPackageId] = useState(null);
  
  // State quản lý trạng thái thanh toán
  const [paymentStatus, setPaymentStatus] = useState("idle"); // idle | processing | success | failed
  const [errorMessage, setErrorMessage] = useState("");

  // Hàm mô phỏng thanh toán
  const handlePayment = () => {
    if (!selectedPackageId) return;

    setPaymentStatus("processing");
    setErrorMessage("");

    // Tìm thông tin gói đã chọn
    const selectedPkg = packages.find(
      (p) => p.subscription_id === selectedPackageId
    );

    // --- BẮT ĐẦU MÔ PHỎNG API CALL ---
    console.log(`Đang xử lý thanh toán cho gói: ${selectedPkg.subscription_name}`);
    setTimeout(() => {
      // Mô phỏng 5% tỷ lệ thất bại
      if (Math.random() < 0.05) {
        setPaymentStatus("failed");
        setErrorMessage("Giao dịch thất bại. Vui lòng thử lại.");
        console.error("Mô phỏng: Thanh toán thất bại.");
      } else {
        // --- MÔ PHỎNG THÀNH CÔNG ---
        setPaymentStatus("success");
        console.log("Mô phỏng: Thanh toán THÀNH CÔNG.");

        // 1. Cập nhật gói hiện tại của user (cập nhật UI)
        const newEndDate = new Date();
        newEndDate.setDate(newEndDate.getDate() + selectedPkg.duration_days);
        
        setCurrentSub({
          user_subscription_id: Math.floor(Math.random() * 10000), // ID ngẫu nhiên
          subscription_id: selectedPkg.subscription_id,
          subscription_name: selectedPkg.subscription_name,
          end_date: newEndDate.toISOString().split("T")[0], // Format: YYYY-MM-DD
        });

        // 2. Gửi thông tin cho User Service (như yêu cầu)
        console.log(
          `%c[GỬI TỚI USER SERVICE]: Cập nhật role cho UserID [123] thành [${selectedPkg.subscription_name}]`,
          "color: blue; font-weight: bold;"
        );
        
        // Reset lựa chọn
        setSelectedPackageId(null);
      }
    }, 2000); // Giả lập 2 giây xử lý
  };

  // Hàm helper để format tiền
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(amount);
  };

  return (
    <motion.div
      className="payment-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="payment-wrapper">
        <h1 className="payment-main-title">Thanh toán & Nâng cấp</h1>

        {/* 1. HIỂN THỊ GÓI HIỆN TẠI */}
        <motion.div
          className="current-plan-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="current-plan-header">
            <Crown size={28} className="current-plan-icon" />
            <h2 className="current-plan-title">Gói Dịch Vụ Hiện Tại</h2>
          </div>
          <p className="current-plan-name">{currentSub.subscription_name}</p>
          <p className="current-plan-date">
            Ngày hết hạn: {currentSub.end_date}
          </p>
        </motion.div>

        {/* 2. CHỌN GÓI NÂNG CẤP */}
        <h2 className="package-selection-title">Chọn gói để nâng cấp</h2>
        <div className="package-selection-container">
          {packages.map((pkg) => {
            const isSelected = selectedPackageId === pkg.subscription_id;
            const isCurrent = currentSub.subscription_id === pkg.subscription_id;

            return (
              <motion.div
                key={pkg.subscription_id}
                className={`package-card ${isSelected ? "selected" : ""} ${
                  isCurrent ? "disabled" : ""
                }`}
                onClick={() => !isCurrent && setSelectedPackageId(pkg.subscription_id)}
                whileHover={{ y: -5 }}
              >
                {isCurrent && (
                  <div className="disabled-overlay">
                    <Prohibit size={32} />
                    <span>Đã sở hữu</span>
                  </div>
                )}
                <h3 className="package-name">{pkg.subscription_name}</h3>
                <p className="package-description">{pkg.description}</p>
                <div className="package-price-duration">
                  <p className="package-price">{formatCurrency(pkg.price)}</p>
                  <p className="package-duration">
                    / {pkg.duration_days} ngày
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* 3. NÚT THANH TOÁN VÀ PHẢN HỒI */}
        <div className="payment-action-area">
          <button
            className="pay-button"
            onClick={handlePayment}
            disabled={!selectedPackageId || paymentStatus === "processing"}
          >
            {paymentStatus === "processing"
              ? "Đang xử lý..."
              : `Thanh toán ${formatCurrency(
                  packages.find((p) => p.subscription_id === selectedPackageId)
                    ?.price || 0
                )}`}
          </button>

          {/* Khu vực hiển thị thông báo động */}
          <AnimatePresence>
            {paymentStatus === "success" && (
              <motion.div
                className="payment-feedback status-success"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <CheckCircle size={24} />
                <span>Thanh toán thành công! Gói của bạn đã được cập nhật.</span>
              </motion.div>
            )}
            {paymentStatus === "failed" && (
              <motion.div
                className="payment-feedback status-failed"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <XCircle size={24} />
                <span>{errorMessage}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default Payment;