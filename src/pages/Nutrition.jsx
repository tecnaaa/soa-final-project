import React, { useState } from "react";
import { motion } from "framer-motion";
// 1. IMPORT FILE CSS MỚI
import "./Nutrition.css";
import {
  Target,
  ForkKnife,
  CookingPot,
  Cookie,
  AppleLogo, // Sử dụng AppleLogo như bạn đã import
} from "phosphor-react";

// Dữ liệu giả lập (giữ nguyên)
const mockMealPlan = {
  meal_plan_id: 1,
  user_id: 1,
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
};

// Helper để lấy icon (đã cập nhật để dùng class CSS)
const getMealIcon = (mealType) => {
  let iconComponent;
  let iconClass = "meal-icon"; // Class chung

  switch (mealType) {
    case "Bữa sáng":
      iconComponent = <CookingPot size={24} />;
      iconClass += " icon-breakfast"; // Class riêng
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
      iconComponent = <AppleLogo size={24} />; // Sửa lỗi: Dùng AppleLogo
      iconClass += " icon-default";
      break;
  }
  // Trả về icon được bọc trong 1 span với class CSS
  return <span className={iconClass}>{iconComponent}</span>;
};

const Nutrition = () => {
  const [mealPlan, setMealPlan] = useState(mockMealPlan);

  const sortedMeals = mealPlan.daily_meals.sort((a, b) =>
    a.meal_time.localeCompare(b.meal_time)
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      // 2. SỬ DỤNG CLASSNAME MỚI
      className="nutrition-container"
    >
      <div className="nutrition-wrapper">
        {/* 1. Thẻ Thông tin chung của Kế hoạch */}
        <motion.div
          className="plan-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <h1 className="plan-title">{mealPlan.plan_name}</h1>
          <div className="plan-targets-container">
            <div className="target-box">
              <Target size={32} className="target-icon icon-calo" />
              <div>
                <span className="target-label">Mục tiêu Calo</span>
                <p className="target-value">
                  {mealPlan.calorie_target_kcal}{" "}
                  <span className="target-unit">kcal</span>
                </p>
              </div>
            </div>
            <div className="target-box">
              <Target size={32} className="target-icon icon-protein" />
              <div>
                <span className="target-label">Mục tiêu Protein</span>
                <p className="target-value">
                  {mealPlan.protein_target_g}{" "}
                  <span className="target-unit">g</span>
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 2. Lưới hiển thị các Bữa ăn hàng ngày */}
        <div className="meal-grid">
          {sortedMeals.map((meal) => (
            <motion.div
              key={meal.daily_meal_id}
              className="meal-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="meal-card-content">
                {/* Tiêu đề Bữa ăn (Loại và Giờ) */}
                <div className="meal-header">
                  <div className="meal-title-group">
                    {getMealIcon(meal.meal_type)}
                    <h2 className="meal-title">{meal.meal_type}</h2>
                  </div>
                  <span className="meal-time-badge">{meal.meal_time}</span>
                </div>

                {/* Danh sách Nguyên liệu (Ingredients) */}
                <ul className="ingredient-list">
                  {meal.ingredients.map((ingredient) => (
                    <li key={ingredient.ingredient_id} className="ingredient-item">
                      <span className="ingredient-name">
                        {ingredient.food_name}
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