import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { LogIn, Mail, Lock, AlertCircle, Leaf } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate   = useNavigate();
  const location   = useLocation();

  const [form, setForm]       = useState({ email: "", password: "" });
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || "/dashboard";

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError("Please enter your email and password.");
      return;
    }
    setLoading(true);
    try {
      await login({ email: form.email, password: form.password });
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (err.response?.status === 401) {
        setError("Invalid email or password. Please try again.");
      } else if (msg) {
        setError(typeof msg === "string" ? msg : "Sign-in failed. Please try again.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left: form panel ── */}
      <div className="flex-1 flex flex-col justify-center px-6 py-12 lg:px-12 bg-white">
        <div className="mx-auto w-full max-w-sm">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 mb-10">
            <span className="flex items-center justify-center w-9 h-9 bg-brand-600 rounded-xl">
              <Leaf className="w-5 h-5 text-white" aria-hidden="true" />
            </span>
            <div className="leading-tight">
              <p className="text-sm font-bold text-neutral-900">AgriMarket</p>
              <p className="text-xs text-neutral-500">Intelligence</p>
            </div>
          </Link>

          <h1 className="text-2xl font-bold text-neutral-900 mb-1">Welcome back</h1>
          <p className="text-sm text-neutral-500 mb-8">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="text-brand-600 font-semibold hover:underline">
              Register here
            </Link>
          </p>

          {error && (
            <div className="alert-error mb-5">
              <AlertCircle size={15} className="shrink-0 mt-0.5" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="form-label" htmlFor="email">Email address</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" aria-hidden="true" />
                <input
                  id="email"
                  type="email"
                  name="email"
                  autoComplete="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  className="form-input pl-9"
                  required
                />
              </div>
            </div>

            <div>
              <label className="form-label" htmlFor="password">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" aria-hidden="true" />
                <input
                  id="password"
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Your password"
                  className="form-input pl-9"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2"
            >
              {loading ? (
                <span className="spinner-sm" aria-hidden="true" />
              ) : (
                <LogIn size={15} aria-hidden="true" />
              )}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>

      {/* ── Right: farm image panel (hidden on small screens) ── */}
      <div className="hidden lg:flex lg:flex-1 relative overflow-hidden bg-brand-700">
        <img
          src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=900&h=1200&fit=crop&auto=format&q=70"
          alt="Lush green farm fields"
          className="absolute inset-0 w-full h-full object-cover opacity-50"
          loading="eager"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-700/80 via-brand-800/60 to-brand-900/80" />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <blockquote className="text-2xl font-bold leading-snug mb-3">
            "Directly from the Farm<br />to Your Hands"
          </blockquote>
          <p className="text-brand-200 text-sm max-w-xs leading-relaxed">
            Compare market prices, get ML-powered recommendations and connect directly with buyers.
          </p>
          <div className="mt-8 flex gap-2">
            {["Markets", "Prediction", "Buyers"].map(t => (
              <span key={t} className="px-3 py-1 rounded-full bg-white/10 text-xs font-medium border border-white/20">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
