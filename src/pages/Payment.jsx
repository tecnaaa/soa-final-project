import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Crown, CheckCircle, XCircle, Prohibit } from "phosphor-react";
import { useAuth } from "../context/AuthContext";
import "./Payment.css";

const Payment = () => {
  const { user } = useAuth();
  const [currentSub, setCurrentSub] = useState(null);
  const [packages, setPackages] = useState([]);
  const [selectedPackageId, setSelectedPackageId] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(true);

  // Fetch subscriptions and current user subscription from API
  useEffect(() => {
    const fetchSubscriptions = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');

        // Fetch available subscriptions
        const subResponse = await fetch('http://localhost:8007/subscription-plans', {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        let availablePackages = [];
        if (subResponse.ok) {
          const subData = await subResponse.json();
          availablePackages = subData.plans || [];
        } else {
          // Fallback mock data
          availablePackages = [
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
        }
        setPackages(availablePackages);

        // Fetch current user subscription
        if (user && user.user_id) {
          const currentSubResponse = await fetch(
            `http://localhost:8007/subscriptions/user/${user.user_id}`,
            {
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              }
            }
          );

          if (currentSubResponse.ok) {
            const currentSubData = await currentSubResponse.json();
            setCurrentSub(currentSubData);
          } else {
            // Fallback - user is on free plan
            setCurrentSub({
              user_subscription_id: null,
              subscription_id: null,
              subscription_name: "Gói Free",
              end_date: "Vĩnh viễn",
            });
          }
        }
      } catch (err) {
        console.error('Error fetching subscriptions:', err);
        // Use fallback mock data
        setPackages([
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
        ]);
        setCurrentSub({
          user_subscription_id: null,
          subscription_id: null,
          subscription_name: "Gói Free",
          end_date: "Vĩnh viễn",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchSubscriptions();
  }, [user]);

  const handlePayment = async () => {
    if (!selectedPackageId) return;

    setPaymentStatus("processing");
    setErrorMessage("");

    const selectedPkg = packages.find((p) => p.subscription_id === selectedPackageId);

    try {
      const token = localStorage.getItem('token');

      // Call Stripe payment intent API
      const paymentResponse = await fetch('http://localhost:8007/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: selectedPkg.price,
          user_id: user.user_id,
          subscription_id: selectedPkg.subscription_id
        })
      });

      if (!paymentResponse.ok) {
        throw new Error('Thanh toán thất bại');
      }

      const paymentData = await paymentResponse.json();

      // In production, would integrate with Stripe here
      // For now, simulate success
      setTimeout(() => {
        setPaymentStatus("success");

        // Update current subscription
        const newEndDate = new Date();
        newEndDate.setDate(newEndDate.getDate() + selectedPkg.duration_days);

        setCurrentSub({
          user_subscription_id: Math.floor(Math.random() * 10000),
          subscription_id: selectedPkg.subscription_id,
          subscription_name: selectedPkg.subscription_name,
          end_date: newEndDate.toISOString().split("T")[0],
        });

        setSelectedPackageId(null);
      }, 2000);

    } catch (err) {
      console.error('Payment error:', err);
      setPaymentStatus("failed");
      setErrorMessage(err.message || "Giao dịch thất bại. Vui lòng thử lại.");
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(amount);
  };

  if (loading) {
    return (
      <motion.div className="payment-container">
        <div>Đang tải dữ liệu...</div>
      </motion.div>
    );
  }

  if (!currentSub) {
    return (
      <motion.div className="payment-container">
        <div>Không thể tải thông tin thanh toán</div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="payment-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="payment-wrapper">
        <h1 className="payment-main-title">Thanh toán & Nâng cấp</h1>

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