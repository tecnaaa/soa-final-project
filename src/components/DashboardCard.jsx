import "./DashboardCard.css";
import { useNavigate } from "react-router-dom";

const DashboardCard = ({ title, value, route }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (route) {
      console.log("Navigating to:", route); // For debugging
      navigate(route);
    }
  };

  return (
    <div
      className="dashboard-card"
      onClick={handleClick}
      style={{ cursor: route ? "pointer" : "default" }}
    >
      <h3>{title}</h3>
      <p>{value}</p>
    </div>
  );
};

export default DashboardCard;
