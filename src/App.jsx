import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import DashboardCard from "./components/DashboardCard";
import ChartSection from "./components/ChartSection";
import RightSidebar from "./components/RightSidebar";
import Login from "./components/LoginForm";
import Counting from "./pages/CaloriesCounting";
import "./App.css";
import Nutrition from "./pages/Nutrition";
import Payment from "./pages/Payment";
import UserProfile from "./pages/UserProfile";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = (credentials) => {
    console.log("Login attempt:", credentials);
    setIsAuthenticated(true);
  };

  if (!isAuthenticated) {
    return (
      <div className="app-wrapper">
        <Login onLogin={handleLogin} />
      </div>
    );
  }

  return (
    <div className="app-wrapper">
      <Router>
        <div className="app-container">
          <Sidebar />
          <div className="main-content">
            <Header />
            <Routes>
              <Route
                path="/"
                element={
                  <div>
                    <div className="cards">
                      <DashboardCard
                        title="Calories"
                        value="1,234"
                        route="/counting" 
                      />
                      <DashboardCard title="Step" value="$12,345" />
                      <DashboardCard title="Heart Rate" value="$12,345" />
                      <DashboardCard title="Sleep" value="321" />
                    </div>
                    <ChartSection />
                  </div>
                }
              />
              <Route path="/counting" element={<Counting />} />
              <Route path="/nutrition" element={<Nutrition />} />
              <Route path="/payment" element={<Payment />} />
              <Route path="/profile" element={<UserProfile />} />
              {/* Redirect tất cả các đường dẫn không xác định về trang chủ */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
          <RightSidebar />
        </div>
      </Router>
    </div>
  );
}
export default App;
