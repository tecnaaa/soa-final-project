import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext"; 
import { workoutAPI } from "../utils/apiServices"; 
import "./RightSidebar.css";
import { Link } from "react-router-dom"; 

const RightSidebar = () => {
  const { user } = useAuth(); 
  const [calendar, setCalendar] = useState([]);
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [userSchedule, setUserSchedule] = useState([]); 
  const [loading, setLoading] = useState(true);

  // Lấy Base URL từ biến môi trường (giống api.js) hoặc mặc định là Gateway
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
  const USERS_SERVICE_URL = 'http://localhost:8002'; // Direct call to Users Service for files

  // Hàm lấy avatar URL - gọi trực tiếp đến Users Service
  const getAvatarUrl = () => {
    if (user && user.user_id) {
      // Endpoint /files/{filename} serve từ backend/uploads/{filename}
      // Nên request /files/1.png sẽ lấy uploads/1.png
      return `http://localhost:8002/files/${user.user_id}.png`;
    }
    // Fallback tạm thời nếu chưa load xong user
    return `http://localhost:8002/files/default.webp`;
  };

  // Hàm tính toán dữ liệu user
  const getUserStats = () => {
    return {
      name: `${user?.first_name || "Guest"} ${user?.last_name || "User"}`,
      email: user?.email || "@guest",
      weight: user?.weight_kg || 70,
      height: user?.height_cm || 175,
      age: 26, 
    };
  };

  // Logic tạo lịch
  useEffect(() => {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();

    setMonth(today.toLocaleString("default", { month: "long" }));
    setYear(currentYear);

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    const temp = [];
    let week = [];

    for (let i = 0; i < firstDay; i++) { week.push(""); }
    for (let day = 1; day <= daysInMonth; day++) {
      week.push(day);
      if (week.length === 7) { temp.push(week); week = []; }
    }
    if (week.length > 0) {
      while (week.length < 7) { week.push(""); }
      temp.push(week);
    }
    setCalendar(temp);
  }, []);

  // Logic Fetch Dữ liệu Lịch Tập
  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      if (!user || !user.user_id) {
        setUserSchedule([
          { name: "Demo Cardio (Mock)", goal: "Endurance", duration: "17–21 Dec" },
          { name: "Demo Yoga (Mock)", goal: "Flexibility", duration: "23–25 Dec" },
        ]);
        setLoading(false);
        return;
      }
      
      try {
        const response = await workoutAPI.getUserPlans(user.user_id); 
        
        if (response.data && Array.isArray(response.data)) {
          setUserSchedule(response.data.slice(0, 2).map(plan => ({
            name: plan.plan_name,
            goal: plan.goal,
            duration: `${plan.duration_weeks} tuần`,
          })));
        } else {
             setUserSchedule([
                { name: "Demo Cardio (Mock)", goal: "Endurance", duration: "17–21 Dec" },
                { name: "Demo Yoga (Mock)", goal: "Flexibility", duration: "23–25 Dec" },
            ]);
        }
      } catch (error) {
        console.error("Error fetching user schedule:", error);
        setUserSchedule([
          { name: "Demo Cardio (Mock)", goal: "Endurance", duration: "17–21 Dec" },
          { name: "Demo Yoga (Mock)", goal: "Flexibility", duration: "23–25 Dec" },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSchedule();
  }, [user]);

  const stats = getUserStats();
  const today = new Date().getDate();

  return (
    <div className="right-sidebar">
      {/* Hồ sơ người dùng */}
      <div className="profile">
        {/* SỬA: Avatar URL logic đơn giản hóa - backend xử lý redirect default */}
        <img 
            src={getAvatarUrl()} 
            alt="User Avatar" 
            className="avatar"
            onError={(e) => { 
              // Nếu lỗi load avatar, fallback về default từ Users Service StaticFiles
              e.target.src = `http://localhost:8002/files/default.webp`; 
            }}
        />
        <div>
          <h3>{stats.name}</h3>
          <p>{stats.email}</p>
        </div>
      </div>

      {/* Thông tin */}
      <div className="user-stats">
        <div><strong>{stats.weight} kg</strong><p>Cân nặng</p></div>
        <div><strong>{stats.height} cm</strong><p>Chiều cao</p></div>
        <div><strong>{stats.age} yrs</strong><p>Tuổi</p></div>
      </div>

      {/* 🗓️ Lịch động */}
      <div className="calendar">
        <h4>{month} {year}</h4>
        <table>
          <thead>
            <tr>
              <th>CN</th><th>T2</th><th>T3</th><th>T4</th><th>T5</th><th>T6</th><th>T7</th>
            </tr>
          </thead>
          <tbody>
            {calendar.map((week, i) => (
              <tr key={i}>
                {week.map((day, j) => (
                  <td
                    key={j}
                    className={day === today ? "today" : ""}
                  >
                    {day}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Lịch tập */}
      <div className="schedule">
        <div className="schedule-header">
          <h4>Lịch tập (Kế hoạch)</h4>
          <Link to="/workout" style={{ color: '#646cff', textDecoration: 'none' }}>Xem tất cả</Link>
        </div>

        {loading ? (
            <p style={{fontSize: '12px', opacity: 0.7}}>Đang tải lịch...</p>
        ) : (
            userSchedule.map((item, index) => (
              <div key={index} className="schedule-item">
                <img src={`https://picsum.photos/60?random=${index}`} alt="workshop" />
                <div>
                  <h5>{item.name}</h5>
                  <p>{item.goal}</p>
                  <small>{item.duration}</small>
                </div>
              </div>
            ))
        )}
        
      </div>
    </div>
  );
};

export default RightSidebar;