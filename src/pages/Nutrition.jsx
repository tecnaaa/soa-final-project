import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import "./Nutrition.css";
import {
  Target,
  ForkKnife,
  CookingPot,
  Cookie,
  AppleLogo,
  Plus,
  X,
  CheckCircle,
  Warning
} from "phosphor-react";
import { useAuth } from "../context/AuthContext";
import { nutritionAPI } from "../utils/apiServices";

// Helper để lấy icon
const getMealIcon = (mealType) => {
  let iconComponent;
  let iconClass = "meal-icon";

  switch (mealType) {
    case "Bữa sáng":
      iconComponent = <CookingPot size={24} />;
      iconClass += " icon-breakfast";
      break;
    case "Bữa trưa":
      iconComponent = <ForkKnife size={24} />;
      iconClass += " icon-lunch";
      break;
    case "Bữa tối":
      iconComponent = <ForkKnife size={24} />;
      iconClass += " icon-dinner";
      break;
    case "Phụ":
      iconComponent = <Cookie size={24} />;
      iconClass += " icon-snack";
      break;
    default:
      iconComponent = <AppleLogo size={24} />;
      iconClass += " icon-default";
      break;
  }
  return <span className={iconClass}>{iconComponent}</span>;
};

const Nutrition = () => {
  const { user } = useAuth();
  const [mealPlans, setMealPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLogMealForm, setShowLogMealForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [formData, setFormData] = useState({
    meal_type: "Bữa sáng",
    food_name: "",
    quantity: "",
    calories: "",
    protein: "",
    carbs: "",
    fats: "",
    log_date: new Date().toISOString().split('T')[0]
  });
  const Nutrition = () => {
    const { user } = useAuth();
    
    // Giả sử role_id: 2=PT, 3=Admin. (Cần đảm bảo AuthContext có trường role_id trong user)
    const canCreateContent = user?.role_id === 2 || user?.role_id === 3;
  
    return (
      // ...
      <div className="nutrition-wrapper">
          {/* CHỈ HIỂN THỊ NÚT TẠO KẾ HOẠCH NẾU CÓ QUYỀN PT/ADMIN */}
          {/* Lưu ý: Nút Log Meal vẫn để cho User dùng */}
          
          {/* ... */}
      </div>
    );
  };

  // Fetch meal plans from API
  useEffect(() => {
    const fetchMealPlans = async () => {
      try {
        setLoading(true);
        if (!user || !user.user_id) {
          throw new Error('User not found');
        }

        const token = localStorage.getItem('token');
        const response = await fetch(
          `http://localhost:8004/meal-plans/user/${user.user_id}`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (response.ok) {
          const plans = await response.json();
          if (Array.isArray(plans) && plans.length > 0) {
            setMealPlans(plans);
            setSelectedPlan(plans[0]);
          } else {
            // Use mock data if no real data
            setMealPlans([getMockMealPlan()]);
            setSelectedPlan(getMockMealPlan());
          }
        } else {
          console.warn('Nutrition API not available, using mock data');
          const mockPlan = getMockMealPlan();
          setMealPlans([mockPlan]);
          setSelectedPlan(mockPlan);
        }
      } catch (err) {
        console.error('Error fetching meal plans:', err);
        const mockPlan = getMockMealPlan();
        setMealPlans([mockPlan]);
        setSelectedPlan(mockPlan);
        setError('Đang sử dụng dữ liệu mẫu');
      } finally {
        setLoading(false);
      }
    };

    fetchMealPlans();
  }, [user]);

  const getMockMealPlan = () => ({
    plan_id: 1,
    user_id: user?.user_id || 1,
    plan_name: "Kế hoạch Giảm mỡ Tuần 1 (2000 kcal)",
    calorie_target_kcal: 2000,
    protein_target_g: 150,
    daily_meals: [
      {
        daily_meal_id: 1,
        meal_plan_id: 1,
        meal_type: "Bữa sáng",
        meal_time: "08:00:00",
        ingredients: [
          { ingredient_id: 1, food_name: "Trứng gà ốp la", quantity: "2 quả" },
          { ingredient_id: 2, food_name: "Bánh mì đen", quantity: "1 lát" },
          { ingredient_id: 3, food_name: "Quả bơ", quantity: "1/2 quả" },
        ],
      },
      {
        daily_meal_id: 2,
        meal_plan_id: 1,
        meal_type: "Bữa trưa",
        meal_time: "12:30:00",
        ingredients: [
          { ingredient_id: 4, food_name: "Ức gà nướng", quantity: "150g" },
          { ingredient_id: 5, food_name: "Gạo lứt", quantity: "100g (đã nấu)" },
          { ingredient_id: 6, food_name: "Rau củ luộc", quantity: "1 đĩa" },
        ],
      },
      {
        daily_meal_id: 3,
        meal_plan_id: 1,
        meal_type: "Bữa tối",
        meal_time: "19:00:00",
        ingredients: [
          { ingredient_id: 7, food_name: "Cá hồi áp chảo", quantity: "150g" },
          { ingredient_id: 8, food_name: "Măng tây nướng", quantity: "100g" },
        ],
      },
      {
        daily_meal_id: 4,
        meal_plan_id: 1,
        meal_type: "Phụ",
        meal_time: "15:00:00",
        ingredients: [
          { ingredient_id: 9, food_name: "Sữa chua Hy Lạp", quantity: "1 hũ" },
          { ingredient_id: 10, food_name: "Hạt hạnh nhân", quantity: "20g" },
        ],
      },
    ],
  });

  const handleLogMealChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogMealSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      if (!user || !user.user_id) {
        throw new Error('User not found');
      }

      // Validate required fields
      if (!formData.food_name || !formData.quantity) {
        setError('Vui lòng nhập tên thực phẩm và số lượng');
        setFormLoading(false);
        return;
      }

      // Prepare data for API
      const mealData = {
        user_id: user.user_id,
        meal_type: formData.meal_type,
        food_name: formData.food_name,
        quantity: formData.quantity,
        calories: formData.calories ? parseInt(formData.calories) : 0,
        protein: formData.protein ? parseFloat(formData.protein) : 0,
        carbs: formData.carbs ? parseFloat(formData.carbs) : 0,
        fats: formData.fats ? parseFloat(formData.fats) : 0,
        log_date: formData.log_date,
        meal_time: new Date().toISOString().split('T')[1].slice(0, 5)
      };

      // Call API
      await nutritionAPI.logMeal(mealData);

      // Success
      setSuccessMessage('Ghi nhận bữa ăn thành công!');
      
      // Reset form
      setFormData({
        meal_type: "Bữa sáng",
        food_name: "",
        quantity: "",
        calories: "",
        protein: "",
        carbs: "",
        fats: "",
        log_date: new Date().toISOString().split('T')[0]
      });

      // Close form after 2 seconds
      setTimeout(() => {
        setShowLogMealForm(false);
        setSuccessMessage(null);
      }, 2000);

    } catch (err) {
      console.error('Error logging meal:', err);
      setError(err.response?.data?.detail || 'Lỗi khi ghi nhận bữa ăn. Vui lòng thử lại.');
    } finally {
      setFormLoading(false);
    }
  };

  if (loading) {
    return (
      <motion.div className="nutrition-container">
        <div>Đang tải dữ liệu kế hoạch dinh dưỡng...</div>
      </motion.div>
    );
  }

  if (!selectedPlan) {
    return (
      <motion.div className="nutrition-container">
        <div>Không có kế hoạch dinh dưỡng nào</div>
      </motion.div>
    );
  }

  const sortedMeals = selectedPlan.daily_meals
    ? [...selectedPlan.daily_meals].sort((a, b) =>
        a.meal_time.localeCompare(b.meal_time)
      )
    : [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="nutrition-container"
    >
      <div className="nutrition-wrapper">
        {error && (
          <motion.div 
            className="error-message error-banner"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Warning size={20} weight="fill" />
            <span>{error}</span>
          </motion.div>
        )}

        {successMessage && (
          <motion.div 
            className="success-message success-banner"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <CheckCircle size={20} weight="fill" />
            <span>{successMessage}</span>
          </motion.div>
        )}

        {mealPlans.length > 1 && (
          <div className="plan-selector">
            <select
              value={selectedPlan.plan_id || 0}
              onChange={(e) => {
                const plan = mealPlans.find(p => p.plan_id === Number(e.target.value));
                setSelectedPlan(plan);
              }}
              className="plan-select"
            >
              <option value="" disabled>Chọn kế hoạch dinh dưỡng</option>
              {mealPlans.map((plan) => (
                <option key={plan.plan_id || plan.meal_plan_id} value={plan.plan_id || plan.meal_plan_id}>
                  {plan.plan_name}
                </option>
              ))}
            </select>
          </div>
        )}

        <motion.div
          className="plan-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="plan-header">
            <h1 className="plan-title">{selectedPlan.plan_name}</h1>
            <button 
              className="log-meal-btn"
              onClick={() => setShowLogMealForm(!showLogMealForm)}
              title="Ghi nhận bữa ăn"
            >
              <Plus size={20} weight="bold" /> Thêm bữa ăn
            </button>
          </div>
          
          <div className="plan-targets-container">
            <div className="target-box">
              <Target size={32} className="target-icon icon-calo" />
              <div>
                <span className="target-label">Mục tiêu Calo</span>
                <p className="target-value">
                  {selectedPlan.calorie_target_kcal || selectedPlan.daily_calories || 2000}{" "}
                  <span className="target-unit">kcal</span>
                </p>
              </div>
            </div>
            <div className="target-box">
              <Target size={32} className="target-icon icon-protein" />
              <div>
                <span className="target-label">Mục tiêu Protein</span>
                <p className="target-value">
                  {selectedPlan.protein_target_g || selectedPlan.daily_protein || 150}{" "}
                  <span className="target-unit">g</span>
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Log Meal Form */}
        {showLogMealForm && (
          <motion.div 
            className="log-meal-form-container"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="log-meal-form-header">
              <h2>Ghi nhận bữa ăn</h2>
              <button 
                className="close-btn"
                onClick={() => setShowLogMealForm(false)}
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleLogMealSubmit} className="log-meal-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="meal_type">Loại bữa ăn *</label>
                  <select
                    id="meal_type"
                    name="meal_type"
                    value={formData.meal_type}
                    onChange={handleLogMealChange}
                    className="form-control"
                  >
                    <option value="Bữa sáng">Bữa sáng</option>
                    <option value="Bữa trưa">Bữa trưa</option>
                    <option value="Bữa tối">Bữa tối</option>
                    <option value="Phụ">Phụ</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="log_date">Ngày *</label>
                  <input
                    id="log_date"
                    type="date"
                    name="log_date"
                    value={formData.log_date}
                    onChange={handleLogMealChange}
                    className="form-control"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="food_name">Tên thực phẩm *</label>
                <input
                  id="food_name"
                  type="text"
                  name="food_name"
                  placeholder="VD: Ức gà nướng"
                  value={formData.food_name}
                  onChange={handleLogMealChange}
                  className="form-control"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="quantity">Số lượng *</label>
                <input
                  id="quantity"
                  type="text"
                  name="quantity"
                  placeholder="VD: 150g hoặc 1 bát"
                  value={formData.quantity}
                  onChange={handleLogMealChange}
                  className="form-control"
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="calories">Calories (kcal)</label>
                  <input
                    id="calories"
                    type="number"
                    name="calories"
                    placeholder="0"
                    value={formData.calories}
                    onChange={handleLogMealChange}
                    className="form-control"
                    min="0"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="protein">Protein (g)</label>
                  <input
                    id="protein"
                    type="number"
                    name="protein"
                    placeholder="0"
                    value={formData.protein}
                    onChange={handleLogMealChange}
                    className="form-control"
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="carbs">Carbs (g)</label>
                  <input
                    id="carbs"
                    type="number"
                    name="carbs"
                    placeholder="0"
                    value={formData.carbs}
                    onChange={handleLogMealChange}
                    className="form-control"
                    min="0"
                    step="0.1"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="fats">Fats (g)</label>
                  <input
                    id="fats"
                    type="number"
                    name="fats"
                    placeholder="0"
                    value={formData.fats}
                    onChange={handleLogMealChange}
                    className="form-control"
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={formLoading}
                >
                  {formLoading ? 'Đang lưu...' : 'Ghi nhận bữa ăn'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowLogMealForm(false)}
                  disabled={formLoading}
                >
                  Hủy
                </button>
              </div>
            </form>
          </motion.div>
        )}

        <div className="meal-grid">
          {sortedMeals.map((meal) => (
            <motion.div
              key={meal.daily_meal_id || meal.meal_id}
              className="meal-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="meal-card-content">
                <div className="meal-header">
                  <div className="meal-title-group">
                    {getMealIcon(meal.meal_type)}
                    <h2 className="meal-title">{meal.meal_type}</h2>
                  </div>
                  <span className="meal-time-badge">{meal.meal_time}</span>
                </div>

                <ul className="ingredient-list">
                  {meal.ingredients && meal.ingredients.map((ingredient) => (
                    <li key={ingredient.ingredient_id || ingredient.id} className="ingredient-item">
                      <span className="ingredient-name">
                        {ingredient.food_name || ingredient.name}
                      </span>
                      <span className="ingredient-quantity">
                        {ingredient.quantity}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default Nutrition;