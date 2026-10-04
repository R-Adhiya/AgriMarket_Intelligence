import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, BarChart3, Lightbulb, User, Leaf, LogOut,
  ShoppingBag, Shield, Menu, X,
} from "lucide-react";
import { ROUTES } from "../constants/routes";
import BackendStatus from "../components/BackendStatus";
import { useAuth } from "../context/AuthContext";

function getNavItems(role) {
  const dashboard = { to: ROUTES.DASHBOARD, icon: LayoutDashboard, label: "Dashboard" };
  const profile   = { to: ROUTES.PROFILE,   icon: User,            label: "Profile"   };

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

function NavItem({ to, icon: Icon, label, onClick }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? "bg-green-50 text-green-700 font-semibold"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        }`
      }
    >
      <Icon className="w-4 h-4 shrink-0" />
      {label}
    </NavLink>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate          = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/");
  }

  const roleLabel = user?.role
    ? user.role.charAt(0) + user.role.slice(1).toLowerCase()
    : "";

  const navItems = getNavItems(user?.role);
  const initials = user?.full_name?.[0]?.toUpperCase() || "U";

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* ── Sidebar (desktop) ── */}
      <aside className="hidden md:flex w-60 shrink-0 bg-white border-r border-gray-200 flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-200">
          <span className="flex items-center justify-center w-8 h-8 bg-green-700 rounded-lg">
            <Leaf className="w-4 h-4 text-white" />
          </span>
          <span className="text-sm font-bold text-gray-900 leading-tight">
            AgriMarket<br />
            <span className="font-normal text-gray-500">Intelligence</span>
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto" aria-label="Main navigation">
          {navItems.map(({ to, icon, label }) => (
            <NavItem key={to} to={to} icon={icon} label={label} />
          ))}
        </nav>

        {/* User footer */}
        {user && (
          <div className="px-4 py-3 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-7 h-7 rounded-full bg-green-700 flex items-center justify-center
                           text-white text-xs font-bold shrink-0"
                aria-hidden="true"
              >
                {initials}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-gray-800 truncate">{user.full_name}</p>
                <p className="text-xs text-gray-400">{roleLabel}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              aria-label="Sign out"
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-gray-500
                         hover:bg-red-50 hover:text-red-600 transition-colors"
            >
              <LogOut size={13} aria-hidden="true" />
              Sign out
            </button>
          </div>
        )}

        <div className="px-4 py-2 border-t border-gray-100">
          <BackendStatus />
        </div>
      </aside>

      {/* ── Mobile top bar ── */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 flex items-center justify-between h-14 px-4">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-7 h-7 bg-green-700 rounded-lg">
            <Leaf className="w-3.5 h-3.5 text-white" />
          </span>
          <span className="text-sm font-bold text-gray-900">AgriMarket</span>
        </div>
        <button
          onClick={() => setMobileOpen((o) => !o)}
          aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
          className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* ── Mobile drawer overlay ── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/30"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Mobile drawer ── */}
      <aside
        className={`md:hidden fixed top-14 left-0 bottom-0 z-40 w-64 bg-white border-r border-gray-200
                   flex flex-col transition-transform duration-200 ease-in-out
                   ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto" aria-label="Mobile navigation">
          {navItems.map(({ to, icon, label }) => (
            <NavItem key={to} to={to} icon={icon} label={label} onClick={() => setMobileOpen(false)} />
          ))}
        </nav>
        {user && (
          <div className="px-4 py-3 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-full bg-green-700 flex items-center justify-center text-white text-xs font-bold shrink-0">
                {initials}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-gray-800 truncate">{user.full_name}</p>
                <p className="text-xs text-gray-400">{roleLabel}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-gray-500
                         hover:bg-red-50 hover:text-red-600 transition-colors"
            >
              <LogOut size={13} />
              Sign out
            </button>
          </div>
        )}
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto md:pt-0 pt-14">
        <Outlet />
      </main>
    </div>
  );
}
