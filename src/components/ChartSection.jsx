// src/ChartSection.jsx
import "./ChartSection.css";
import mockChartData from "./data.js";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Custom Tooltip để hiển thị thông tin khi di chuột
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    // payload[0] là Calories In, payload[1] là Calories Out
    const caloriesIn = payload[0].value;
    const caloriesOut = payload[1].value;
    const netCalories = caloriesIn - caloriesOut;

    return (
      <div className="custom-tooltip">
        <p className="label">{`Ngày: ${label}`}</p>
        <p style={{ color: '#646cff' } }>{`Calo In: ${caloriesIn} Kcal`}</p>
        <p style={{ color: '#333333' }}>{`Calo Out: ${caloriesOut} Kcal`}</p>
        <p className="net-calories">{`Thặng dư/Thâm hụt: ${netCalories} Kcal`}</p>
      </div>
    );
  }

  return null;
};


export default function ChartSection() {
  return (
    <div className="chart-section">
      <h2>Biểu đồ Hoạt động (Tuần này)</h2>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={mockChartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis label={{ value: 'Kcal', angle: -90, position: 'insideLeft' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {/* Thanh biểu đồ cho Calo In */}
            <Bar dataKey="calories_in" fill="#8884d8" name="Calo In (Tiêu thụ)" />
            {/* Thanh biểu đồ cho Calo Out */}
            <Bar dataKey="calories_out" fill="#82ca9d" name="Calo Out (Đốt cháy)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}