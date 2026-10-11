import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus, Mail, Lock, Phone, User, AlertCircle, CheckCircle, Leaf } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ROLES = [
  { value: "FARMER", label: "🌾 Farmer", desc: "Sell crops, get recommendations" },
  { value: "BUYER",  label: "🛒 Buyer",  desc: "Source produce from farmers"     },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate      = useNavigate();

  const [form, setForm] = useState({
    full_name: "", email: "", phone: "", password: "", confirm: "", role: "FARMER",
  });
  const [errors, setErrors]     = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
    setApiError("");
  }

  function validate() {
    const errs = {};
    if (!form.full_name.trim() || form.full_name.trim().length < 2)
      errs.full_name = "Full name must be at least 2 characters.";
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/))
      errs.email = "Please enter a valid email address.";
    if (form.password.length < 8)
      errs.password = "Password must be at least 8 characters.";
    else if (!/[A-Za-z]/.test(form.password))
      errs.password = "Password must contain at least one letter.";
    else if (!/\d/.test(form.password))
      errs.password = "Password must contain at least one number.";
    if (form.password !== form.confirm)
      errs.confirm = "Passwords do not match.";
    return errs;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      await register({
        full_name: form.full_name.trim(),
        email:     form.email.trim().toLowerCase(),
        phone:     form.phone.trim() || undefined,
        password:  form.password,
        role:      form.role,
      });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (err.response?.status === 409) {
        setApiError("An account with this email already exists.");
      } else if (err.response?.status === 422) {
        const details = err.response.data?.detail;
        setApiError(Array.isArray(details) ? details.map((d) => d.msg).join(" ") : (msg || "Validation error."));
      } else {
        setApiError(msg || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-brand-50 flex flex-col justify-center items-center px-4">
        <div className="card card-body max-w-sm w-full text-center">
          <CheckCircle size={44} className="mx-auto text-brand-600 mb-3" aria-hidden="true" />
          <h2 className="text-lg font-bold text-neutral-900">Account created!</h2>
          <p className="text-sm text-neutral-500 mt-1">Redirecting you to the login page…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left: farm image (desktop only) ── */}
      <div className="hidden lg:flex lg:flex-1 relative overflow-hidden bg-brand-700">
        <img
          src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=900&h=1200&fit=crop&auto=format&q=70"
          alt="Indian farmer in a green field"
          className="absolute inset-0 w-full h-full object-cover opacity-50"
          loading="eager"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-700/80 via-brand-800/60 to-brand-900/80" />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <p className="text-xs font-semibold tracking-widest text-lime-300 uppercase mb-3">
            AgriMarket Intelligence
          </p>
          <blockquote className="text-2xl font-bold leading-snug mb-3">
            Smart Decisions.<br />Better Markets.<br />Higher Returns.
          </blockquote>
          <p className="text-brand-200 text-sm max-w-xs leading-relaxed">
            Join farmers and buyers using data-driven market intelligence to get better deals.
          </p>
        </div>
      </div>

      {/* ── Right: form panel ── */}
      <div className="flex-1 flex flex-col justify-center px-6 py-10 lg:px-12 bg-white overflow-y-auto">
        <div className="mx-auto w-full max-w-sm">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 mb-8">
            <span className="flex items-center justify-center w-9 h-9 bg-brand-600 rounded-xl">
              <Leaf className="w-5 h-5 text-white" aria-hidden="true" />
            </span>
            <div className="leading-tight">
              <p className="text-sm font-bold text-neutral-900">AgriMarket</p>
              <p className="text-xs text-neutral-500">Intelligence</p>
            </div>
          </Link>

          <h1 className="text-2xl font-bold text-neutral-900 mb-1">Create your account</h1>
          <p className="text-sm text-neutral-500 mb-6">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">
              Sign in
            </Link>
          </p>

          {/* Role selector */}
          <div className="mb-5">
            <p className="form-label">I am a</p>
            <div className="grid grid-cols-2 gap-3">
              {ROLES.map((r) => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setForm((p) => ({ ...p, role: r.value }))}
                  className={`p-3 rounded-xl border-2 text-left transition-all duration-150
                    ${form.role === r.value
                      ? "border-brand-600 bg-brand-50 text-brand-700"
                      : "border-neutral-200 text-neutral-600 hover:border-neutral-300 bg-white"
                    }`}
                >
                  <p className="text-sm font-semibold">{r.label}</p>
                  <p className="text-xs text-neutral-400 mt-0.5">{r.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {apiError && (
            <div className="alert-error mb-4">
              <AlertCircle size={15} className="shrink-0 mt-0.5" aria-hidden="true" />
              <span>{apiError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Field icon={<User size={14} />}  label="Full Name"          name="full_name" type="text"     value={form.full_name} onChange={handleChange} placeholder="Adhiya Kumar"                    error={errors.full_name} />
            <Field icon={<Mail size={14} />}  label="Email address"      name="email"     type="email"    value={form.email}     onChange={handleChange} placeholder="you@example.com"                  error={errors.email} />
            <Field icon={<Phone size={14} />} label="Phone (optional)"   name="phone"     type="tel"      value={form.phone}     onChange={handleChange} placeholder="9876543210"                       error={errors.phone} />
            <Field icon={<Lock size={14} />}  label="Password"           name="password"  type="password" value={form.password}  onChange={handleChange} placeholder="Min. 8 chars, 1 letter, 1 number" error={errors.password} />
            <Field icon={<Lock size={14} />}  label="Confirm password"   name="confirm"   type="password" value={form.confirm}   onChange={handleChange} placeholder="Re-enter your password"            error={errors.confirm} />

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? <span className="spinner-sm" aria-hidden="true" /> : <UserPlus size={15} aria-hidden="true" />}
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Field({ icon, label, name, type, value, onChange, placeholder, error }) {
  return (
    <div>
      <label className="form-label" htmlFor={name}>{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" aria-hidden="true">
          {icon}
        </span>
        <input
          id={name}
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`form-input pl-9 ${error ? "border-red-400 focus:ring-red-400" : ""}`}
        />
      </div>
      {error && (
        <p className="form-error" role="alert">
          <AlertCircle size={12} aria-hidden="true" /> {error}
        </p>
      )}
    </div>
  );
}
