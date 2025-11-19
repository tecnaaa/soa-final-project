import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import DashboardCard from "./components/DashboardCard";
import ChartSection from "./components/ChartSection";
import RightSidebar from "./components/RightSidebar";
import Login from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import ResetPasswordForm from "./components/ResetPasswordForm";
import Counting from "./pages/CaloriesCounting";
import Nutrition from "./pages/Nutrition";
import Payment from "./pages/Payment";
import UserProfile from "./pages/UserProfile";
import Workout from "./pages/Workout";
import LoadingSpinner from "./components/LoadingSpinner";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <div className="app-wrapper">
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route path="/reset-password" element={<ResetPasswordForm />} />
            
            {/* Protected routes */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
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
                                  apiEndpoint="http://localhost:8005/logs/user/1"
                                />
                                <DashboardCard 
                                  title="Step" 
                                  value="$12,345"
                                  apiEndpoint="http://localhost:8003/progress/user/1"
                                />
                                <DashboardCard 
                                  title="Heart Rate" 
                                  value="$12,345"
                                />
                                <DashboardCard 
                                  title="Sleep" 
                                  value="321"
                                />
                              </div>
                              <ChartSection />
                            </div>
                          }
                        />
                        <Route path="/counting" element={<Counting />} />
                        <Route path="/nutrition" element={<Nutrition />} />
                        <Route path="/payment" element={<Payment />} />
                        <Route path="/profile" element={<UserProfile />} />
                        <Route path="/workout" element={<Workout />} />
                      </Routes>
                    </div>
                    <RightSidebar />
                  </div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </Router>
      </div>
    </AuthProvider>
  );
}

export default App;
