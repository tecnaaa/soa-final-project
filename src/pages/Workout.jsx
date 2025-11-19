import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Barbell, 
  Timer, 
  Fire, 
  Plus, 
  Notebook, 
  PlayCircle,
  Lightning,
  Warning
} from "phosphor-react";
import { useAuth } from "../context/AuthContext";
import { workoutAPI } from "../utils/apiServices";
import "./Workout.css";

const Workout = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("plans");
  const [plans, setPlans] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock data để hiển thị đẹp ngay cả khi chưa tạo data trong DB
  const mockPlans = [
    {
      plan_id: 991,
      plan_name: "Full Body Beginner",
      difficulty: "beginner",
      duration_weeks: 4,
      sessions_per_week: 3,
      goal: "General Fitness"
    },
    {
      plan_id: 992,
      plan_name: "Upper Body Power",
      difficulty: "intermediate",
      duration_weeks: 8,
      sessions_per_week: 4,
      goal: "Muscle Gain"
    }
  ];

  const mockExercises = [
    {
      exercise_id: 101,
      name: "Push Up",
      difficulty: "beginner",
      primary_muscle_group_id: 1,
      primary_muscle: { name: "Chest", muscle_group_id: 1 },
      equipment: { name: "Bodyweight", equipment_id: 1 }
    },
    {
      exercise_id: 102,
      name: "Squat",
      difficulty: "intermediate",
      primary_muscle_group_id: 2,
      primary_muscle: { name: "Legs", muscle_group_id: 2 },
      equipment: { name: "Barbell", equipment_id: 2 }
    },
    {
      exercise_id: 103,
      name: "Deadlift",
      difficulty: "advanced",
      primary_muscle_group_id: 3,
      primary_muscle: { name: "Back", muscle_group_id: 3 },
      equipment: { name: "Barbell", equipment_id: 2 }
    }
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!user || !user.user_id) {
          console.warn("User not found, using mock data");
          if (activeTab === "plans") setPlans(mockPlans);
          else setExercises(mockExercises);
          return;
        }

        if (activeTab === "plans") {
          try {
            const res = await workoutAPI.getUserPlans(user.user_id);
            // Nếu API trả về rỗng hoặc lỗi, dùng mock để demo giao diện
            setPlans(res.data && res.data.length > 0 ? res.data : mockPlans);
          } catch (err) {
            console.error("Error fetching user plans:", err);
            setError("Không thể tải kế hoạch. Hiển thị dữ liệu mẫu.");
            setPlans(mockPlans);
          }
        } else if (activeTab === "exercises") {
          try {
            // Truyền user_id để API có thể filter theo subscription
            const res = await workoutAPI.getExercises({ user_id: user.user_id });
            setExercises(res.data && res.data.length > 0 ? res.data : mockExercises);
          } catch (err) {
            console.error("Error fetching exercises:", err);
            setError("Không thể tải bài tập. Hiển thị dữ liệu mẫu.");
            setExercises(mockExercises);
          }
        }
      } catch (error) {
        console.error("Error in fetchData:", error);
        setError("Lỗi khi tải dữ liệu. Vui lòng thử lại.");
        if (activeTab === "plans") setPlans(mockPlans);
        else setExercises(mockExercises);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, activeTab]);

  // Helper để render badge độ khó
  const DifficultyBadge = ({ level }) => (
    <span className={`badge ${level?.toLowerCase() || 'beginner'}`}>
      {level || 'Beginner'}
    </span>
  );

  // Helper để lấy tên nhóm cơ
  const getPrimaryMuscleName = (exercise) => {
    if (!exercise.primary_muscle) return "Unknown";
    if (typeof exercise.primary_muscle === "object") {
      return exercise.primary_muscle.name || "Unknown";
    }
    return exercise.primary_muscle;
  };

  // Helper để lấy tên dụng cụ
  const getEquipmentName = (exercise) => {
    if (!exercise.equipment) return "Bodyweight";
    if (typeof exercise.equipment === "object") {
      return exercise.equipment.name || "Bodyweight";
    }
    return exercise.equipment;
  };

  const Workout = () => {
    const { user } = useAuth();
    const canCreateContent = user?.role_id === 2 || user?.role_id === 3;
  
    return (
      <div className="workout-container">
        <div className="workout-wrapper">
          <div className="workout-header">
            <h1 className="workout-title">...</h1>
            
            {/* CHỈ HIỂN THỊ NÚT TẠO KẾ HOẠCH NẾU CÓ QUYỀN */}
            {canCreateContent && (
                <button className="start-btn">
                  <Plus size={20} weight="bold" /> Tạo kế hoạch mới
                </button>
            )}
          </div>
          {/* ... */}
        </div>
      </div>
    );
  };

  return (
    <div className="workout-container">
      <div className="workout-wrapper">
        
        {/* Header */}
        <div className="workout-header">
          <h1 className="workout-title">
            <Barbell size={36} weight="duotone" />
            Tập Luyện & Thể Hình
          </h1>
          <button className="start-btn" style={{ width: 'auto', padding: '10px 20px' }}>
            <Plus size={20} weight="bold" /> Tạo kế hoạch mới
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <motion.div 
            className="error-message"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Warning size={20} weight="fill" />
            <span>{error}</span>
          </motion.div>
        )}

        {/* Tabs Navigation */}
        <div className="workout-tabs">
          <button 
            className={`tab-btn ${activeTab === "plans" ? "active" : ""}`}
            onClick={() => setActiveTab("plans")}
          >
            <Notebook size={20} /> Kế hoạch của tôi
          </button>
          <button 
            className={`tab-btn ${activeTab === "exercises" ? "active" : ""}`}
            onClick={() => setActiveTab("exercises")}
          >
            <Lightning size={20} /> Thư viện bài tập
          </button>
        </div>

        {/* Content Area */}
        {loading ? (
          <div className="loading-state">Đang tải dữ liệu...</div>
        ) : (
          <motion.div 
            className="workout-grid"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Render Plans */}
            {activeTab === "plans" && plans.length > 0 ? (
              plans.map((plan) => (
                <div key={plan.plan_id} className="workout-card">
                  <div className="card-header">
                    <div>
                      <h3 className="card-title">{plan.plan_name}</h3>
                      <p className="card-subtitle">{plan.goal || "No goal specified"}</p>
                    </div>
                    <DifficultyBadge level={plan.difficulty} />
                  </div>
                  
                  <div className="card-details">
                    <div className="detail-item">
                      <Timer size={18} />
                      <span>{plan.duration_weeks || 0} tuần</span>
                    </div>
                    <div className="detail-item">
                      <Fire size={18} />
                      <span>{plan.sessions_per_week || 0} buổi/tuần</span>
                    </div>
                  </div>

                  <button className="start-btn">
                    <PlayCircle size={24} /> Bắt đầu tập
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-state">
                {activeTab === "plans" ? "Bạn chưa có kế hoạch nào. Hãy tạo một kế hoạch mới!" : "Không có kế hoạch nào"}
              </div>
            )}

            {/* Render Exercises */}
            {activeTab === "exercises" && exercises.length > 0 ? (
              exercises.map((ex) => (
                <div key={ex.exercise_id} className="workout-card">
                  <div className="exercise-img-placeholder">
                    <Barbell size={48} weight="thin" />
                  </div>
                  <div className="card-header">
                    <div>
                      <h3 className="card-title">{ex.name}</h3>
                      <p className="card-subtitle">
                        Nhóm cơ: {getPrimaryMuscleName(ex)}
                      </p>
                    </div>
                    <DifficultyBadge level={ex.difficulty} />
                  </div>
                  <p style={{ fontSize: '0.9rem', color: '#aaa', marginBottom: '15px' }}>
                    Dụng cụ: {getEquipmentName(ex)}
                  </p>
                  <button className="start-btn" style={{ background: 'rgba(255,255,255,0.1)' }}>
                    Xem hướng dẫn
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-state">
                {activeTab === "exercises" ? "Không tìm thấy bài tập nào" : ""}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Workout;