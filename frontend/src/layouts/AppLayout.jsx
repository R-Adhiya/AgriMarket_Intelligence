import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, BarChart3, Lightbulb, User, Leaf, LogOut,
  ShoppingBag, Shield,
} from "lucide-react";
import { ROUTES } from "../constants/routes";
import BackendStatus from "../components/BackendStatus";
import { useAuth } from "../context/AuthContext";

function getNavItems(role) {
  const dashboard = { to: ROUTES.DASHBOARD, icon: LayoutDashboard, label: "Dashboard" };
  const profile   = { to: ROUTES.PROFILE,   icon: User,            label: "Profile" };

  if (role === "ADMIN") {
    return [
      dashboard,
      { to: ROUTES.ADMIN, icon: Shield, label: "Admin Panel" },
      profile,
    ];
  }

  if (role === "FARMER") {
    return [
      dashboard,
      { to: ROUTES.MARKETS,         icon: TrendingUp,  label: "Markets"             },
      { to: ROUTES.PREDICTION,      icon: BarChart3,   label: "Price Prediction"    },
      { to: ROUTES.RECOMMENDATIONS, icon: Lightbulb,   label: "Recommendations"     },
      { to: ROUTES.BUYERS,          icon: ShoppingBag, label: "Buyer Opportunities" },
      profile,
    ];
  }

  if (role === "BUYER") {
    return [
      dashboard,
      { to: ROUTES.BUYERS, icon: ShoppingBag, label: "My Requirements" },
      profile,
    ];
  }

  return [dashboard, profile];
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate          = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  const roleLabel = user?.role
    ? user.role.charAt(0) + user.role.slice(1).toLowerCase()
    : "";

  const navItems = getNavItems(user?.role);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-200">
          <span className="flex items-center justify-center w-8 h-8 bg-green-700 rounded-lg">
            <Leaf className="w-4 h-4 text-white" />
          </span>
          <span className="text-sm font-semibold text-gray-900 leading-tight">
            AgriMarket<br />Intelligence
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User info + logout */}
        {user && (
          <div className="px-4 py-3 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold uppercase">
                {user.full_name?.[0] || "U"}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-gray-800 truncate">{user.full_name}</p>
                <p className="text-xs text-gray-400">{roleLabel}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-gray-500
                         hover:bg-red-50 hover:text-red-600 transition"
            >
              <LogOut size={13} />
              Sign out
            </button>
          </div>
        )}

        {/* Backend status */}
        <div className="px-4 py-2 border-t border-gray-100">
          <BackendStatus />
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
