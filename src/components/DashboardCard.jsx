import "./DashboardCard.css";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

const DashboardCard = ({ title, value, route, apiEndpoint }) => {
  const navigate = useNavigate();
  const [displayValue, setDisplayValue] = useState(value);
  const [loading, setLoading] = useState(false);

  // Gọi API nếu có endpoint được cung cấp
  useEffect(() => {
    if (apiEndpoint) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const token = localStorage.getItem('token');
          const response = await fetch(apiEndpoint, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            const data = await response.json();
            
            // Xử lý dữ liệu tùy theo loại card
            if (title === "Calories") {
              // Lấy tổng calories hôm nay từ API
              const totalCalories = data.total_calories || data.calories || "0";
              setDisplayValue(totalCalories);
            } else if (title === "Step") {
              // Lấy bước hôm nay
              const steps = data.steps || data.count || "0";
              setDisplayValue(steps);
            } else if (title === "Heart Rate") {
              // Lấy nhịp tim trung bình
              const heartRate = data.heart_rate || data.avg_heart_rate || "0";
              setDisplayValue(heartRate);
            } else if (title === "Sleep") {
              // Lấy thời gian ngủ
              const sleep = data.sleep || data.hours || "0";
              setDisplayValue(sleep);
            }
          } else {
            // Nếu API fail, giữ mock value
            console.warn(`Failed to fetch ${title} data`);
          }
        } catch (err) {
          console.error(`Error fetching ${title}:`, err);
          // Nếu error, giữ mock value
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }
  }, [apiEndpoint, title]);

  const handleClick = () => {
    if (route) {
      console.log("Navigating to:", route);
      navigate(route);
    }
  };

  return (
    <div
      className="dashboard-card"
      onClick={handleClick}
      style={{ cursor: route ? "pointer" : "default" }}
    >
      <h3>{title}</h3>
      <p>{loading ? "..." : displayValue}</p>
    </div>
  );
};

export default DashboardCard;
