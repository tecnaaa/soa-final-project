import React, { useState, useEffect } from "react";
import "./RightSidebar.css";

const RightSidebar = () => {
  const [calendar, setCalendar] = useState([]);
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");

  // ✅ Tạo lịch tự động khi component load
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

    // Thêm ô trống trước ngày đầu tháng
    for (let i = 0; i < firstDay; i++) {
      week.push("");
    }

    // Lặp qua ngày trong tháng
    for (let day = 1; day <= daysInMonth; day++) {
      week.push(day);
      if (week.length === 7) {
        temp.push(week);
        week = [];
      }
    }

    // Thêm ô trống cuối tháng
    if (week.length > 0) {
      while (week.length < 7) {
        week.push("");
      }
      temp.push(week);
    }

    setCalendar(temp);
  }, []);

  const today = new Date().getDate();

  return (
    <div className="right-sidebar">
      {/* Hồ sơ người dùng */}
      <div className="profile">
        <img src="https://i.pravatar.cc/100" alt="User" className="avatar" />
        <div>
          <h3>Lionel Messi</h3>
          <p>@itsworks</p>
        </div>
      </div>

      {/* Thông tin */}
      <div className="user-stats">
        <div><strong>75 kg</strong><p>Weight</p></div>
        <div><strong>180 cm</strong><p>Height</p></div>
        <div><strong>26 yrs</strong><p>Age</p></div>
      </div>

      {/* 🗓️ Lịch động */}
      <div className="calendar">
        <h4>{month} {year}</h4>
        <table>
          <thead>
            <tr>
              <th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th>
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
          <h4>Scheduled</h4>
          <span>View all</span>
        </div>

        <div className="schedule-item">
          <img src="https://picsum.photos/80" alt="workshop" />
          <div>
            <h5>Cardio Workshop</h5>
            <p>Strengthens your muscles</p>
            <small>17–21 Dec</small>
          </div>
        </div>

        <div className="schedule-item">
          <img src="https://picsum.photos/81" alt="workshop" />
          <div>
            <h5>Yoga Class</h5>
            <p>Improves flexibility</p>
            <small>23–25 Dec</small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RightSidebar;
