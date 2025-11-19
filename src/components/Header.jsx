import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Header.css";

export default function Header() {
  const [time, setTime] = useState(new Date());
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1>Your Tracking</h1>
      </div>
      <div className="header-right">
        <div className="clock">{formatTime(time)}</div>
        <div className="user-info">
          <span className="user-name">{user?.first_name} {user?.last_name}</span>
          <button onClick={handleLogout} className="logout-btn">Đăng xuất</button>
        </div>
      </div>
    </header>
  );
}
