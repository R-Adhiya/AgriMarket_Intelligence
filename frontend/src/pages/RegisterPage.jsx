import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus, Mail, Lock, Phone, User, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ROLES = [
  { value: "FARMER", label: "Farmer" },
  { value: "BUYER",  label: "Buyer" },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate      = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email:     "",
    phone:     "",
    password:  "",
    confirm:   "",
    role:      "FARMER",
  });
  const [errors, setErrors]   = useState({});
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
        if (Array.isArray(details)) {
          setApiError(details.map((d) => d.msg).join(" "));
        } else {
          setApiError(msg || "Validation error. Please check your input.");
        }
      } else {
        setApiError(msg || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-8 py-10 max-w-sm w-full text-center">
          <CheckCircle size={40} className="mx-auto text-green-600 mb-3" />
          <h3 className="text-lg font-semibold text-gray-900">Account created!</h3>
          <p className="text-sm text-gray-500 mt-1">Redirecting you to the login page…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <Link to="/" className="inline-flex items-center gap-2">
          <span className="text-2xl font-bold text-green-700">AgriMarket</span>
          <span className="text-2xl font-semibold text-gray-700">Intelligence</span>
        </Link>
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Create your account</h2>
        <p className="mt-1 text-sm text-gray-500">
          Already have an account?{" "}
          <Link to="/login" className="text-green-700 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white shadow-sm rounded-xl border border-gray-200 px-8 py-8">
          {apiError && (
            <div className="mb-4 flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{apiError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full name */}
            <Field
              icon={<User size={16} />}
              label="Full Name"
              name="full_name"
              type="text"
              value={form.full_name}
              onChange={handleChange}
              placeholder="Adhiya Kumar"
              error={errors.full_name}
            />

            {/* Email */}
            <Field
              icon={<Mail size={16} />}
              label="Email address"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              error={errors.email}
            />

            {/* Phone (optional) */}
            <Field
              icon={<Phone size={16} />}
              label="Phone number (optional)"
              name="phone"
              type="tel"
              value={form.phone}
              onChange={handleChange}
              placeholder="9876543210"
              error={errors.phone}
            />

            {/* Password */}
            <Field
              icon={<Lock size={16} />}
              label="Password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Min. 8 chars, 1 letter, 1 number"
              error={errors.password}
            />

            {/* Confirm password */}
            <Field
              icon={<Lock size={16} />}
              label="Confirm password"
              name="confirm"
              type="password"
              value={form.confirm}
              onChange={handleChange}
              placeholder="Re-enter your password"
              error={errors.confirm}
            />

            {/* Account type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account type
              </label>
              <div className="flex gap-3">
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setForm((p) => ({ ...p, role: r.value }))}
                    className={`flex-1 py-2 rounded-lg border text-sm font-medium transition
                      ${form.role === r.value
                        ? "border-green-600 bg-green-50 text-green-700"
                        : "border-gray-300 text-gray-600 hover:border-gray-400"
                      }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-green-700 hover:bg-green-800
                         disabled:bg-green-400 text-white font-medium py-2.5 rounded-lg transition"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <UserPlus size={16} />
              )}
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Shared field component ────────────────────────────────────────────────────
function Field({ icon, label, name, type, value, onChange, placeholder, error }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">{icon}</span>
        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full pl-9 pr-4 py-2.5 border rounded-lg text-sm
                      focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent
                      ${error ? "border-red-400 bg-red-50" : "border-gray-300"}`}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
