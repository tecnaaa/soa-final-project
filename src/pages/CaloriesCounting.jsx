import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Flame, Knife, Activity, Calculator } from "phosphor-react";
import { calorieAPI } from "../utils/api";
import "./CaloriesCounting.css";

// Define thresholds as constants
const THRESHOLD_GOOD_BURN = -500;
const THRESHOLD_BALANCE = 100;

const CaloriesCounting = () => {
  const [foodList, setFoodList] = useState([]);
  const [selectedFood, setSelectedFood] = useState("");
  const [foodWeight, setFoodWeight] = useState("");
  const [exerciseCalories, setExerciseCalories] = useState("");
  const [foodCalories, setFoodCalories] = useState(0);
  const [calorieBalance, setCalorieBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch foods from API
  useEffect(() => {
    const fetchFoods = async () => {
      try {
        setLoading(true);
        // Gọi API để lấy danh sách thực phẩm từ Calories Service
        const response = await fetch('http://localhost:8005/foods/', {
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (response.ok) {
          const foods = await response.json();
          setFoodList(Array.isArray(foods) ? foods : []);
        } else {
          // Fallback to mock data nếu API không hoạt động
          console.warn('Calories API not available, using mock data');
          setFoodList([
            { food_id: 1, name: "Cơm trắng", calories_per_100g: 130 },
            { food_id: 2, name: "Thịt gà", calories_per_100g: 239 },
            { food_id: 3, name: "Thịt bò", calories_per_100g: 250 },
            { food_id: 4, name: "Cá hồi", calories_per_100g: 208 },
            { food_id: 5, name: "Trứng gà", calories_per_100g: 155 },
            { food_id: 6, name: "Rau cải", calories_per_100g: 32 },
            { food_id: 7, name: "Gạo lức", calories_per_100g: 111 },
            { food_id: 8, name: "Bánh mì", calories_per_100g: 265 },
          ]);
        }
      } catch (err) {
        console.error('Error fetching foods:', err);
        // Use fallback mock data
        setFoodList([
          { food_id: 1, name: "Cơm trắng", calories_per_100g: 130 },
          { food_id: 2, name: "Thịt gà", calories_per_100g: 239 },
          { food_id: 3, name: "Thịt bò", calories_per_100g: 250 },
          { food_id: 4, name: "Cá hồi", calories_per_100g: 208 },
          { food_id: 5, name: "Trứng gà", calories_per_100g: 155 },
          { food_id: 6, name: "Rau cải", calories_per_100g: 32 },
          { food_id: 7, name: "Gạo lức", calories_per_100g: 111 },
          { food_id: 8, name: "Bánh mì", calories_per_100g: 265 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchFoods();
  }, []);

  const calculateFoodCalories = () => {
    const food = foodList.find((f) => f.food_id === Number(selectedFood) || f.id === Number(selectedFood));
    if (food && foodWeight) {
      const caloriesPerGram = (food.calories_per_100g || food.caloriesPer100g) / 100;
      const calories = caloriesPerGram * Number(foodWeight);
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

  if (loading) {
    return <div className="calories-container"><div>Đang tải dữ liệu...</div></div>;
  }

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

        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label className="form-label">
            <Knife size={20} /> Chọn thực phẩm
          </label>
          <select
            value={selectedFood}
            onChange={(e) => setSelectedFood(e.target.value)}
            className="form-select"
          >
            <option value="" disabled>Chọn loại thức ăn</option>
            {foodList.map((food) => (
              <option key={food.food_id || food.id} value={food.food_id || food.id}>
                {food.name} ({food.calories_per_100g || food.caloriesPer100g} kcal/100g)
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
