import { Link } from "react-router-dom";
import {
  Leaf, TrendingUp, BarChart3, Lightbulb, Users, UserCircle,
  ArrowRight, Menu, X, CheckCircle,
} from "lucide-react";
import { useState } from "react";
import { ROUTES } from "../constants/routes";

const features = [
  {
    icon: TrendingUp,
    title: "Market Intelligence",
    description: "Compare crop prices across agricultural markets in real time to know exactly where demand is highest.",
  },
  {
    icon: BarChart3,
    title: "Price Prediction",
    description: "Use machine learning to estimate future crop prices and plan your selling window ahead of time.",
  },
  {
    icon: Lightbulb,
    title: "Smart Recommendations",
    description: "Identify the best market based on expected net return after factoring in transport costs.",
  },
  {
    icon: Users,
    title: "Buyer Marketplace",
    description: "Discover verified buyers posting requirements and connect directly to secure the best deal.",
  },
  {
    icon: UserCircle,
    title: "Farmer Profiles",
    description: "Manage your farm, crops, and availability so the right buyers can find you.",
  },
  {
    icon: Leaf,
    title: "Direct Connections",
    description: "Skip the middlemen. Send and receive interest requests and see contact details after acceptance.",
  },
];

const farmerBenefits = [
  "Compare live prices across multiple markets",
  "Get ML-powered price forecasts",
  "Receive smart market recommendations",
  "Connect directly with verified buyers",
  "Track all buyer opportunities in one place",
];

const buyerBenefits = [
  "Post crop requirements with your price",
  "See farmers matching your needs instantly",
  "Send interest requests directly to farmers",
  "Get contact details after acceptance",
  "Track all your procurement in one dashboard",
];

const navLinks = [
  { label: "Features", to: "#features" },
  { label: "For Farmers", to: "#farmers" },
  { label: "For Buyers", to: "#buyers" },
];

export default function LandingPage() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          {/* Logo */}
          <Link to={ROUTES.HOME} className="flex items-center gap-2.5 shrink-0" aria-label="AgriMarket Intelligence home">
            <span className="flex items-center justify-center w-8 h-8 bg-brand-600 rounded-lg">
              <Leaf className="w-4 h-4 text-white" aria-hidden="true" />
            </span>
            <span className="font-bold text-gray-900 text-[15px]">AgriMarket Intelligence</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Landing page navigation">
            {navLinks.map(({ label, to }) => (
              <a
                key={label}
                href={to}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                {label}
              </a>
            ))}
          </nav>

          {/* CTA + mobile toggle */}
          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              to="/login"
              className="hidden sm:inline-flex items-center text-sm font-medium text-gray-700
                         hover:text-gray-900 transition-colors px-3 py-2"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center gap-1.5 text-sm font-medium bg-brand-600 text-white
                         px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
            >
              Get started
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </Link>
            <button
              className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
              onClick={() => setMobileOpen((o) => !o)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav drawer */}
        {mobileOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1">
            {navLinks.map(({ label, to }) => (
              <a
                key={label}
                href={to}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2.5 rounded-lg text-sm text-gray-700 hover:bg-gray-50 font-medium"
              >
                {label}
              </a>
            ))}
            <div className="pt-2 border-t border-gray-100 flex gap-2">
              <Link
                to="/login"
                onClick={() => setMobileOpen(false)}
                className="flex-1 text-center px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileOpen(false)}
                className="flex-1 text-center px-3 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700"
              >
                Register
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero ── */}
      <section className="flex-none relative overflow-hidden">
        {/* Background farm image */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=1400&h=700&fit=crop&auto=format&q=60"
            alt=""
            aria-hidden="true"
            className="w-full h-full object-cover"
            loading="eager"
            decoding="async"
          />
          {/* Overlay: light gradient so text stays readable */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/90 via-white/80 to-white/95" />
        </div>

        <div className="relative z-10 py-20 sm:py-28 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600
                             bg-brand-50 px-3 py-1 rounded-full mb-6">
              <Leaf className="w-3.5 h-3.5" aria-hidden="true" />
              Agricultural Technology Platform
            </span>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 tracking-tight
                           leading-[1.1] max-w-3xl mx-auto">
              Directly from the Farm<br className="hidden sm:block" />
              <span className="text-brand-600"> to Your Hands</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
              AgriMarket Intelligence helps farmers compare markets, understand price trends,
              get smart recommendations, and connect directly with buyers — no middlemen required.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3
                           bg-brand-600 text-white font-semibold rounded-xl hover:bg-brand-700
                           transition-colors shadow-sm text-sm"
              >
                Join as Farmer or Buyer
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3
                           border border-gray-300 text-gray-700 font-semibold rounded-xl
                           hover:bg-gray-50 transition-colors text-sm"
              >
                Sign in to your account
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Crop Showcase ── */}
      <section className="py-10 px-4 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest text-center mb-6">
            Supported crops
          </p>
          <div className="flex items-center justify-center gap-4 sm:gap-6 flex-wrap">
            {[
              { name: "Tomato",  url: "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=80&h=80&fit=crop&auto=format&q=75" },
              { name: "Onion",   url: "https://images.unsplash.com/photo-1587049352851-8d4e89133924?w=80&h=80&fit=crop&auto=format&q=75" },
              { name: "Potato",  url: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=80&h=80&fit=crop&auto=format&q=75" },
              { name: "Rice",    url: "https://images.unsplash.com/photo-1536304993881-ff86e0c9b1b5?w=80&h=80&fit=crop&auto=format&q=75" },
              { name: "Banana",  url: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=80&h=80&fit=crop&auto=format&q=75" },
            ].map(({ name, url }) => (
              <div key={name} className="flex flex-col items-center gap-2">
                <div className="w-14 h-14 rounded-full overflow-hidden border-2 border-gray-100 shadow-sm">
                  <img
                    src={url}
                    alt={`${name} crop`}
                    width={56}
                    height={56}
                    loading="lazy"
                    decoding="async"
                    className="w-full h-full object-cover"
                  />
                </div>
                <span className="text-xs text-gray-500 font-medium">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-20 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">Everything you need to sell smarter</h2>
            <p className="mt-3 text-gray-500 max-w-xl mx-auto text-[15px] leading-relaxed">
              A complete platform built around the real challenges farmers and buyers face at every harvest.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-xl border border-gray-200 bg-white p-6 hover:shadow-md hover:border-brand-200
                           transition-all duration-200"
              >
                <span className="inline-flex items-center justify-center w-10 h-10 bg-brand-50 rounded-xl mb-4">
                  <Icon className="w-5 h-5 text-brand-600" aria-hidden="true" />
                </span>
                <h3 className="font-semibold text-gray-900 mb-1.5 text-[15px]">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── For Farmers ── */}
      <section id="farmers" className="py-20 px-4 bg-brand-50/50">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600
                               bg-brand-50 px-3 py-1 rounded-full mb-4">
                For Farmers
              </span>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Make every harvest count
              </h2>
              <p className="text-gray-600 text-[15px] mb-6 leading-relaxed">
                Stop guessing which market to sell in. Get data-driven recommendations,
                see price trends, and connect directly with verified buyers.
              </p>
              <ul className="space-y-3">
                {farmerBenefits.map((b) => (
                  <li key={b} className="flex items-start gap-2.5">
                    <CheckCircle className="w-4 h-4 text-brand-600 mt-0.5 shrink-0" aria-hidden="true" />
                    <span className="text-sm text-gray-700">{b}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="mt-8 inline-flex items-center gap-2 bg-brand-600 text-white font-semibold
                           px-5 py-2.5 rounded-xl hover:bg-brand-700 transition-colors text-sm"
              >
                Register as Farmer
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
              <div className="rounded-xl overflow-hidden mb-4 -mx-2 -mt-2">
                <img
                  src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600&h=220&fit=crop&auto=format&q=70"
                  alt="Indian farmer in a green field"
                  width={600}
                  height={220}
                  loading="lazy"
                  decoding="async"
                  className="w-full h-36 object-cover"
                />
              </div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                Sample Recommendation
              </h3>
              <div className="bg-brand-50 border border-brand-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-brand-600 font-medium">Recommended Market</span>
                  <span className="text-xs bg-brand-600 text-white px-2 py-0.5 rounded-full">Best Return</span>
                </div>
                <p className="text-lg font-bold text-gray-900">Erode APMC</p>
                <p className="text-sm text-gray-500">Tamil Nadu · 85 km</p>
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  { label: "Price", value: "₹30/kg" },
                  { label: "Transport", value: "₹1,200" },
                  { label: "Net Revenue", value: "₹13,800" },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-sm font-bold text-gray-900 mt-0.5">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── For Buyers ── */}
      <section id="buyers" className="py-20 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="order-2 md:order-1 bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-3">
              <div className="rounded-xl overflow-hidden -mx-2 -mt-2 mb-3">
                <img
                  src="https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=600&h=200&fit=crop&auto=format&q=70"
                  alt="Fresh vegetables at an agricultural market"
                  width={600}
                  height={200}
                  loading="lazy"
                  decoding="async"
                  className="w-full h-32 object-cover"
                />
              </div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                Active Requirement
              </h3>
              <div className="border border-gray-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-900">Tomato</span>
                  <span className="text-xs bg-brand-50 text-brand-600 border border-brand-200 px-2 py-0.5 rounded-md font-semibold">ACTIVE</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-gray-500">
                  <div><span className="text-gray-400">Qty</span><br /><strong className="text-gray-800">500 kg</strong></div>
                  <div><span className="text-gray-400">Price</span><br /><strong className="text-gray-800">₹30/kg</strong></div>
                  <div><span className="text-gray-400">Location</span><br /><strong className="text-gray-800">Coimbatore</strong></div>
                </div>
              </div>
              <p className="text-xs text-gray-400 text-center">12 matching farmers found</p>
            </div>
            <div className="order-1 md:order-2">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700
                               bg-blue-50 px-3 py-1 rounded-full mb-4">
                For Buyers
              </span>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Source directly from farmers
              </h2>
              <p className="text-gray-600 text-[15px] mb-6 leading-relaxed">
                Post your requirements and get matched with the right farmers.
                Skip the wholesale chain and build reliable supply relationships.
              </p>
              <ul className="space-y-3">
                {buyerBenefits.map((b) => (
                  <li key={b} className="flex items-start gap-2.5">
                    <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" aria-hidden="true" />
                    <span className="text-sm text-gray-700">{b}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="mt-8 inline-flex items-center gap-2 bg-gray-900 text-white font-semibold
                           px-5 py-2.5 rounded-xl hover:bg-gray-800 transition-colors text-sm"
              >
                Register as Buyer
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-100 bg-gray-50 py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-7 h-7 bg-brand-600 rounded-lg">
                <Leaf className="w-3.5 h-3.5 text-white" aria-hidden="true" />
              </span>
              <div>
                <p className="font-bold text-gray-900 text-sm">AgriMarket Intelligence</p>
                <p className="text-xs text-gray-500">Smart Decisions. Better Markets. Higher Returns.</p>
              </div>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <Link to="/login" className="hover:text-gray-900 transition-colors">Sign in</Link>
              <Link to="/register" className="hover:text-gray-900 transition-colors">Register</Link>
            </div>
          </div>
          <div className="border-t border-gray-200 pt-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-400">
            <p>© 2024 AgriMarket Intelligence. All rights reserved.</p>
            <p>Built for farmers and buyers across India.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
