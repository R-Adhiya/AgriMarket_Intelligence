import { Link } from 'react-router-dom'
import {
  Leaf, TrendingUp, BarChart3, Lightbulb, Users, UserCircle,
  ArrowRight, Menu, X
} from 'lucide-react'
import { useState } from 'react'
import { ROUTES } from '../constants/routes'
import BackendStatus from '../components/BackendStatus'

const features = [
  {
    icon: UserCircle,
    title: 'Farmer Management',
    description: 'Manage farmer profiles, farms, crops, and selling information in one place.',
  },
  {
    icon: TrendingUp,
    title: 'Market Intelligence',
    description: 'Compare crop prices across different agricultural markets in real time.',
  },
  {
    icon: BarChart3,
    title: 'Price Prediction',
    description: 'Use machine learning to estimate future crop prices and plan ahead.',
  },
  {
    icon: Lightbulb,
    title: 'Smart Recommendations',
    description: 'Identify the best markets and selling windows based on expected net returns.',
  },
  {
    icon: Users,
    title: 'Buyer Marketplace',
    description: 'Allow farmers and buyers to discover suitable selling opportunities together.',
  },
]

const navLinks = [
  { label: 'Home',             to: ROUTES.HOME           },
  { label: 'Markets',          to: ROUTES.MARKETS        },
  { label: 'Price Prediction', to: ROUTES.PREDICTION     },
  { label: 'About',            to: '#about'              },
]

export default function LandingPage() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          {/* Logo */}
          <Link to={ROUTES.HOME} className="flex items-center gap-2.5 shrink-0">
            <span className="flex items-center justify-center w-8 h-8 bg-primary-600 rounded-lg">
              <Leaf className="w-4 h-4 text-white" />
            </span>
            <span className="font-semibold text-gray-900">AgriMarket Intelligence</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map(({ label, to }) => (
              <Link
                key={label}
                to={to}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                {label}
              </Link>
            ))}
          </nav>

          {/* Login / Register + mobile toggle */}
          <div className="flex items-center gap-3">
            <Link
              to="/register"
              className="hidden sm:inline-flex text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Register
            </Link>
            <Link
              to="/login"
              className="hidden sm:inline-flex btn-secondary text-sm py-2 px-4"
            >
              Login
            </Link>
            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileOpen((o) => !o)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav drawer */}
        {mobileOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1">
            {navLinks.map(({ label, to }) => (
              <Link
                key={label}
                to={to}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
              >
                {label}
              </Link>
            ))}
            <Link
              to="/login"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-lg text-sm font-medium text-green-700 hover:bg-green-50"
            >
              Login
            </Link>
          </div>
        )}
      </header>

      {/* ── Hero ── */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20 sm:py-28 bg-gradient-to-b from-primary-50/60 to-white">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-primary-700 bg-primary-100 px-3 py-1 rounded-full mb-6">
          <Leaf className="w-3.5 h-3.5" />
          Agricultural Technology Platform
        </span>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight max-w-3xl leading-tight">
          Make Smarter Decisions<br className="hidden sm:block" /> for Every Harvest
        </h1>
        <p className="mt-6 text-lg text-gray-600 max-w-2xl">
          AgriMarket Intelligence helps farmers compare markets, understand price trends,
          estimate returns, and connect with buyers.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center gap-3">
          <Link to={ROUTES.MARKETS} className="btn-primary">
            Explore Market Intelligence
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to={ROUTES.DASHBOARD} className="btn-secondary">
            Go to Dashboard
          </Link>
        </div>
        {/* Backend status — shows integration health on the landing page */}
        <div className="mt-8">
          <BackendStatus />
        </div>
      </section>

      {/* ── Features ── */}
      <section id="about" className="py-20 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">Everything you need to sell smarter</h2>
            <p className="mt-3 text-gray-600 max-w-xl mx-auto">
              A complete platform built around the real challenges farmers face at every harvest.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="card p-6 hover:shadow-md transition-shadow">
                <span className="inline-flex items-center justify-center w-10 h-10 bg-primary-100 rounded-lg mb-4">
                  <Icon className="w-5 h-5 text-primary-700" />
                </span>
                <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
                <p className="text-sm text-gray-600">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-100 bg-gray-50 py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Leaf className="w-4 h-4 text-primary-600" />
            <span className="font-medium text-gray-700">AgriMarket Intelligence</span>
          </div>
          <p>Smart Decisions. Better Markets. Higher Returns.</p>
          <p>Phase 1 — Project Setup &amp; Architecture</p>
        </div>
      </footer>
    </div>
  )
}
