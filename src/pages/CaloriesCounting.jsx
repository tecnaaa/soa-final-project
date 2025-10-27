import React, { useState } from "react";
import { motion } from "framer-motion";
import { Flame, Knife, Activity, Calculator } from "phosphor-react";
import "./CaloriesCounting.css";

// Define thresholds as constants
const THRESHOLD_GOOD_BURN = -500; // Ngưỡng đốt calo tốt
const THRESHOLD_BALANCE = 100;    // Ngưỡng cân bằng

const FOOD_DATABASE = [
  { id: 1, name: "Cơm trắng", caloriesPer100g: 130 },
  { id: 2, name: "Thịt gà", caloriesPer100g: 239 },
  { id: 3, name: "Thịt bò", caloriesPer100g: 250 },
  { id: 4, name: "Cá hồi", caloriesPer100g: 208 },
  { id: 5, name: "Trứng gà", caloriesPer100g: 155 },
  { id: 6, name: "Rau cải", caloriesPer100g: 32 },
  { id: 7, name: "Gạo lức", caloriesPer100g: 111 },
  { id: 8, name: "Bánh mì", caloriesPer100g: 265 },
];

const CaloriesCounting = () => {
  const [selectedFood, setSelectedFood] = useState("");
  const [foodWeight, setFoodWeight] = useState("");
  const [exerciseCalories, setExerciseCalories] = useState("");
  const [foodCalories, setFoodCalories] = useState(0);
  const [calorieBalance, setCalorieBalance] = useState(null);

  const calculateFoodCalories = () => {
    const food = FOOD_DATABASE.find((f) => f.id === Number(selectedFood));
    if (food && foodWeight) {
      const calories = (food.caloriesPer100g * Number(foodWeight)) / 100;
      setFoodCalories(calories);
      return calories;
    }
    return 0;
  };

  const getCalorieMessage = (balance) => {
    if (balance < THRESHOLD_GOOD_BURN) {
      return {
        text: "Đốt Calo Rất Tốt! 🔥",
        color: "text-green-500",
        description: "Bạn đang trong quá trình đốt calo tích cực!",
      };
    } else if (balance < 0) {
      return {
        text: "Đốt Calo Tốt! 💪",
        color: "text-blue-500",
        description: "Tiếp tục duy trì nhé!",
      };
    } else if (balance <= THRESHOLD_BALANCE) {
      return {
        text: "Cân bằng Năng lượng ⚖️",
        color: "text-yellow-500",
        description: "Bạn đang duy trì cân bằng năng lượng.",
      };
    } else {
      return {
        text: "Dư Năng Lượng! ⚠️",
        color: "text-red-500",
        description: "Hãy vận động nhiều hơn để đốt calo nhé!",
      };
    }
  };

  const handleCalculate = () => {
    const caloriesIn = calculateFoodCalories();
    const caloriesOut = Number(exerciseCalories) || 0;
    const netCalories = caloriesIn - caloriesOut;
    setCalorieBalance(netCalories);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="calories-container"
    >
      <div className="calories-card">
        <h2 className="calories-title">
          <Flame size={28} color="#60a5fa" /> Calories Counting
        </h2>

        <div className="form-group">
          <label className="form-label">
            <Knife size={20} /> Chọn thực phẩm
          </label>
          <select
            value={selectedFood}
            onChange={(e) => setSelectedFood(e.target.value)}
            className="form-select"
          >
            <option value="">Chọn loại thức ăn</option>
            {FOOD_DATABASE.map((food) => (
              <option key={food.id} value={food.id}>
                {food.name} ({food.caloriesPer100g} kcal/100g)
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">
            <Knife size={20} /> Khối lượng (gram)
          </label>
          <input
            type="number"
            placeholder="Ví dụ: 100"
            value={foodWeight}
            onChange={(e) => setFoodWeight(e.target.value)}
            className="form-input"
          />
        </div>

        {foodCalories > 0 && (
          <div className="calories-result">
            <p className="calories-value">
              Lượng calories: {foodCalories.toFixed(1)} kcal
            </p>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">
            <Activity size={20} /> Calo tiêu hao do tập luyện (kcal)
          </label>
          <input
            type="number"
            placeholder="Ví dụ: 500"
            value={exerciseCalories}
            onChange={(e) => setExerciseCalories(e.target.value)}
            className="form-input"
          />
        </div>

        <button onClick={handleCalculate} className="calculate-btn">
          <Calculator size={20} /> Tính toán
        </button>

        {/* Calorie Balance Results */}
        {calorieBalance !== null && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="results-section"
          >
            <div className="balance-info">
              <h3 className="text-xl font-semibold mb-2">Kết quả:</h3>
              <div
                className={`message ${getCalorieMessage(calorieBalance).color}`}
              >
                <p className="text-lg font-bold">
                  {getCalorieMessage(calorieBalance).text}
                </p>
                <p className="text-sm mt-1">
                  {getCalorieMessage(calorieBalance).description}
                </p>
              </div>
              <div className="stats mt-4">
                <p className="text-md">
                  Năng lượng nạp vào:{" "}
                  <span className="font-semibold">
                    {foodCalories.toFixed(1)} kcal
                  </span>
                </p>
                <p className="text-md">
                  Năng lượng tiêu hao:{" "}
                  <span className="font-semibold">{exerciseCalories} kcal</span>
                </p>
                <p className="text-md mt-2">
                  Cân bằng năng lượng:{" "}
                  <span
                    className={`font-bold ${
                      calorieBalance > 0 ? "text-red-500" : "text-green-500"
                    }`}
                  >
                    {calorieBalance.toFixed(1)} kcal
                  </span>
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default CaloriesCounting;
