// src/ChartSection.jsx
import "./ChartSection.css";
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
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
    const caloriesIn = payload[0].value;
    const caloriesOut = payload[1].value;
    const netCalories = caloriesIn - caloriesOut;

    return (
      <div className="custom-tooltip">
        <p className="label">{`Ngày: ${label}`}</p>
        <p style={{ color: '#646cff' }}>{`Calo In: ${caloriesIn} Kcal`}</p>
        <p style={{ color: '#333333' }}>{`Calo Out: ${caloriesOut} Kcal`}</p>
        <p className="net-calories">{`Thặng dư/Thâm hụt: ${netCalories} Kcal`}</p>
      </div>
    );
  }

  return null;
};

// Mock data fallback nếu API không hoạt động
const getMockChartData = () => [
  {
    "day": "Thứ 2",
    "calories_in": 2200,
    "calories_out": 450,
    "net_calories": 1750
  },
  {
    "day": "Thứ 3",
    "calories_in": 1950,
    "calories_out": 600,
    "net_calories": 1350
  },
  {
    "day": "Thứ 4",
    "calories_in": 2500,
    "calories_out": 350,
    "net_calories": 2150
  },
  {
    "day": "Thứ 5",
    "calories_in": 1800,
    "calories_out": 700,
    "net_calories": 1100
  },
  {
    "day": "Thứ 6",
    "calories_in": 2050,
    "calories_out": 550,
    "net_calories": 1500
  },
  {
    "day": "Thứ 7",
    "calories_in": 2100,
    "calories_out": 400,
    "net_calories": 1700
  },
  {
    "day": "CN",
    "calories_in": 1900,
    "calories_out": 650,
    "net_calories": 1250
  }
];

export default function ChartSection() {
  const { user } = useAuth();
  const [chartData, setChartData] = useState(getMockChartData());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch data từ API
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!user || !user.user_id) {
          setChartData(getMockChartData());
          setLoading(false);
          return;
        }

        const token = localStorage.getItem('token');
        
        // Gọi API để lấy dữ liệu 7 ngày gần đây
        const response = await fetch(
          `http://localhost:8005/logs/user/${user.user_id}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.ok) {
          const data = await response.json();
          
          // Xử lý dữ liệu từ API
          if (Array.isArray(data)) {
            // Nếu API trả về array các logs, chuyển đổi thành format chart
            const processedData = data.map((log, index) => ({
              day: `Ngày ${index + 1}`,
              calories_in: log.actual_calories || log.total_calories || 0,
              calories_out: log.burned_calories || 0,
              net_calories: (log.actual_calories || log.total_calories || 0) - (log.burned_calories || 0)
            }));
            
            // Chỉ lấy 7 ngày gần đây
            const last7Days = processedData.slice(-7);
            setChartData(last7Days.length > 0 ? last7Days : getMockChartData());
          } else {
            setChartData(getMockChartData());
          }
        } else {
          console.warn('Failed to fetch chart data from API, using mock data');
          setChartData(getMockChartData());
        }
      } catch (err) {
        console.error('Error fetching chart data:', err);
        setError('Không thể tải dữ liệu biểu đồ');
        setChartData(getMockChartData());
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [user]);

  return (
    <div className="chart-section">
      <h2>Biểu đồ Hoạt động (Tuần này)</h2>
      {error && <div className="error-message">{error}</div>}
      {loading ? (
        <div className="loading-chart">Đang tải dữ liệu biểu đồ...</div>
      ) : (
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis label={{ value: 'Kcal', angle: -90, position: 'insideLeft' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="calories_in" fill="#8884d8" name="Calo In (Tiêu thụ)" />
              <Bar dataKey="calories_out" fill="#82ca9d" name="Calo Out (Đốt cháy)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}