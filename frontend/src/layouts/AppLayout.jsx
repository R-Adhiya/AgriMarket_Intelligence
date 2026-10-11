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
        isActive ? "nav-item-active" : "nav-item-inactive"
      }
    >
      <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
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

  // Sidebar content shared between desktop & mobile
  const SidebarContent = ({ onItemClick } = {}) => (
    <>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-brand-600">
        <span className="flex items-center justify-center w-8 h-8 bg-lime-400 rounded-xl shrink-0">
          <Leaf className="w-4 h-4 text-brand-700" aria-hidden="true" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-bold text-white">AgriMarket</p>
          <p className="text-xs text-brand-300">Intelligence</p>
        </div>
      </div>

      {/* Role chip */}
      <div className="px-5 py-2">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold
                         bg-lime-400/20 text-lime-300 border border-lime-400/30">
          {roleLabel}
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto" aria-label="Main navigation">
        {navItems.map(({ to, icon, label }) => (
          <NavItem key={to} to={to} icon={icon} label={label} onClick={onItemClick} />
        ))}
      </nav>

      {/* User footer */}
      {user && (
        <div className="px-4 py-3 border-t border-brand-600/60">
          <div className="flex items-center gap-2 mb-2.5">
            <div
              className="w-8 h-8 rounded-full bg-lime-400 flex items-center justify-center
                         text-brand-700 text-xs font-bold shrink-0"
              aria-hidden="true"
            >
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user.full_name}</p>
              <p className="text-xs text-brand-300/80">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            aria-label="Sign out"
            className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs
                       text-brand-300 hover:bg-red-500/10 hover:text-red-300
                       transition-colors duration-150"
          >
            <LogOut size={13} aria-hidden="true" />
            Sign out
          </button>
        </div>
      )}

      <div className="px-4 py-2 border-t border-brand-600/40">
        <BackendStatus />
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-neutral-100 overflow-hidden">
      {/* ── Desktop sidebar ── */}
      <aside className="hidden md:flex w-60 shrink-0 bg-brand-700 flex-col">
        <SidebarContent />
      </aside>

      {/* ── Mobile top bar ── */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-brand-700 flex items-center justify-between h-14 px-4">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-7 h-7 bg-lime-400 rounded-lg">
            <Leaf className="w-3.5 h-3.5 text-brand-700" aria-hidden="true" />
          </span>
          <span className="text-sm font-bold text-white">AgriMarket</span>
        </div>
        <button
          onClick={() => setMobileOpen((o) => !o)}
          aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={mobileOpen}
          className="p-2 rounded-lg text-brand-200 hover:bg-brand-600 transition-colors"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* ── Mobile overlay ── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/40 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Mobile drawer ── */}
      <aside
        className={`md:hidden fixed top-14 left-0 bottom-0 z-40 w-64 bg-brand-700 flex flex-col
                   transition-transform duration-200 ease-in-out
                   ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <SidebarContent onItemClick={() => setMobileOpen(false)} />
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto md:pt-0 pt-14">
        <Outlet />
      </main>
    </div>
  );
}
