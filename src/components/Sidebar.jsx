import "./Sidebar.css";
import { Link } from "react-router-dom";

import { Calendar, Leaf, Flame, User, CreditCard, UserCircle, Barbell} from "phosphor-react";
function GlassIconComp({ Icon, label }) {
  return (
    <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-3 flex flex-col items-center hover:bg-white/20 transition-colors">
      <Icon size={28} color="white" />
      <span className="mt-1 text-white text-xs">{label}</span>
    </div>
  );
}
export default function Sidebar() {
  return (
    <div className="sidebar">
      <Link to="/" className="logo-link">
        <h2 className="logo">🏋️</h2>
      </Link>
      <ul>
        <li>
          <Link to="/counting">
            <GlassIconComp Icon={Flame} />
          </Link>
        </li>
        <li>
          <Link to="/nutrition">
            <GlassIconComp Icon={Leaf} />
          </Link>
        </li>
        <li>
          <Link to="/profile">
            <GlassIconComp Icon={User} />
          </Link>
        </li>
        <li>
          <Link to="/payment">
            <GlassIconComp Icon={CreditCard} />
          </Link>
        </li>
        <li>
          <Link to="/workout">
            <GlassIconComp Icon={Barbell} />
          </Link>
        </li>
        <li>
          <GlassIconComp Icon={UserCircle} />
        </li>
      </ul>
    </div>
  );
}
