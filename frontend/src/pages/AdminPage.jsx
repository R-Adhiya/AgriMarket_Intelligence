import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  Users, Leaf, ShoppingBag, TrendingUp, Lightbulb, MessageSquare,
  RefreshCw, AlertCircle, CheckCircle2, XCircle, Clock, Shield,
  ToggleLeft, ToggleRight, ChevronLeft, ChevronRight, ShieldCheck, Search,
} from "lucide-react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend,
} from "recharts";
import { useAuth } from "../context/AuthContext";
import {
  getAdminDashboard, getAdminUsers, updateUserStatus,
  getAdminFarmers, getAdminBuyers, getAdminMarkets, getAdminActivity,
} from "../services/adminService";
import PageHeader from "../components/PageHeader";

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

const PIE_COLORS = ["#047857", "#2563eb", "#d97706", "#dc2626", "#7c3aed"];

function StatCard({ icon: Icon, label, value, color = "green" }) {
  const colors = {
    green:  "bg-brand-50 text-brand-600",
    blue:   "bg-blue-50 text-blue-700",
    amber:  "bg-amber-50 text-amber-700",
    purple: "bg-purple-50 text-purple-700",
    rose:   "bg-rose-50 text-rose-700",
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
      <span className={`flex items-center justify-center w-10 h-10 rounded-lg shrink-0 ${colors[color]}`}>
        <Icon className="w-5 h-5" />
      </span>
      <div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <p className="text-xl font-bold text-gray-900">{value ?? "—"}</p>
      </div>
    </div>
  );
}

function Badge({ status }) {
  const map = {
    true:  { label: "Active",   cls: "bg-brand-50 text-brand-600" },
    false: { label: "Inactive", cls: "bg-red-50 text-red-600" },
    FARMER: { label: "Farmer", cls: "bg-brand-50 text-brand-600" },
    BUYER:  { label: "Buyer",  cls: "bg-blue-50 text-blue-700" },
    ADMIN:  { label: "Admin",  cls: "bg-purple-50 text-purple-700" },
    PENDING:  { label: "Pending",  cls: "bg-amber-50 text-amber-700" },
    ACCEPTED: { label: "Accepted", cls: "bg-brand-50 text-brand-600" },
    REJECTED: { label: "Rejected", cls: "bg-red-50 text-red-600" },
    registration: { label: "Signup",      cls: "bg-blue-50 text-blue-700" },
    recommendation: { label: "Rec",       cls: "bg-amber-50 text-amber-700" },
    requirement:    { label: "Req",        cls: "bg-purple-50 text-purple-700" },
    interest:       { label: "Interest",   cls: "bg-brand-50 text-brand-600" },
  };
  const entry = map[String(status)] ?? { label: String(status), cls: "bg-gray-100 text-gray-600" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${entry.cls}`}>
      {entry.label}
    </span>
  );
}

function SectionCard({ title, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function Loading() {
  return (
    <div className="flex items-center justify-center py-10 text-sm text-gray-400 gap-2">
      <RefreshCw className="w-4 h-4 animate-spin" /> Loading…
    </div>
  );
}

function ErrorMsg({ onRetry }) {
  return (
    <div className="flex flex-col items-center py-8 gap-2 text-sm text-red-500">
      <AlertCircle className="w-5 h-5" /> Unable to load this section.
      {onRetry && <button onClick={onRetry} className="text-xs text-gray-400 hover:underline">Retry</button>}
    </div>
  );
}

function Empty({ msg = "No data yet." }) {
  return <p className="text-sm text-gray-400 text-center py-6">{msg}</p>;
}

function Paginator({ page, total, pageSize, onChange }) {
  const pages = Math.ceil(total / pageSize);
  if (pages <= 1) return null;
  return (
    <div className="flex items-center justify-end gap-2 mt-3 text-sm text-gray-500">
      <button onClick={() => onChange(page - 1)} disabled={page <= 1}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-30">
        <ChevronLeft className="w-4 h-4" />
      </button>
      <span>Page {page} / {pages}</span>
      <button onClick={() => onChange(page + 1)} disabled={page >= pages}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-30">
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

const TABS = ["Overview", "Users", "Farmers", "Buyers", "Markets", "Crop Suggestions", "Activity"];

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function AdminPage() {
  const { user } = useAuth();

  if (!user) return <Navigate to="/" />;
  if (user.role !== "ADMIN") return <Navigate to="/dashboard" />;

  const [tab, setTab] = useState("Overview");

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-5">
      <PageHeader
        icon={Shield}
        title="Admin Dashboard"
        subtitle="Monitor and manage the AgriMarket Intelligence platform"
      />

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview"         && <OverviewTab />}
      {tab === "Users"            && <UsersTab />}
      {tab === "Farmers"          && <FarmersTab />}
      {tab === "Buyers"           && <BuyersTab />}
      {tab === "Markets"          && <MarketsTab />}
      {tab === "Crop Suggestions" && <CropSuggestionsTab />}
      {tab === "Activity"         && <ActivityTab />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overview Tab
// ---------------------------------------------------------------------------

function OverviewTab() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    getAdminDashboard()
      .then(d => setData(d.stats))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <Loading />;
  if (error)   return <ErrorMsg onRetry={load} />;
  if (!data)   return null;

  const roleData = [
    { name: "Farmers", value: data.total_farmers },
    { name: "Buyers",  value: data.total_buyers },
    { name: "Admins",  value: data.total_admins },
  ].filter(d => d.value > 0);

  const interestData = [
    { name: "Pending",  value: data.pending_interests },
    { name: "Accepted", value: data.accepted_interests },
    { name: "Rejected", value: data.rejected_interests },
  ].filter(d => d.value > 0);

  const reqData = [
    { name: "Active",    value: data.active_requirements },
    { name: "Fulfilled", value: data.fulfilled_requirements },
    { name: "Other",     value: Math.max(0, data.total_requirements - data.active_requirements - data.fulfilled_requirements) },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-5">
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <StatCard icon={Users}       label="Total Users"        value={data.total_users}         color="green" />
        <StatCard icon={Leaf}        label="Farmers"            value={data.total_farmers}       color="green" />
        <StatCard icon={ShoppingBag} label="Buyers"             value={data.total_buyers}        color="blue" />
        <StatCard icon={TrendingUp}  label="Markets"            value={data.total_markets}       color="amber" />
        <StatCard icon={TrendingUp}  label="Price Records"      value={data.total_price_records} color="amber" />
        <StatCard icon={Lightbulb}   label="Recommendations"    value={data.total_recommendations} color="purple" />
        <StatCard icon={MessageSquare} label="Interest Requests" value={data.total_interests}   color="rose" />
        <StatCard icon={ShoppingBag}  label="Active Requirements" value={data.active_requirements} color="blue" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SectionCard title="Users by Role">
          {roleData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={roleData} cx="50%" cy="50%" outerRadius={65} dataKey="value" label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                  {roleData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <Empty msg="No user data." />}
        </SectionCard>

        <SectionCard title="Interest Request Status">
          {interestData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={interestData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                  {interestData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty msg="No interest data." />}
        </SectionCard>

        <SectionCard title="Buyer Requirement Status">
          {reqData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={reqData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#047857" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty msg="No requirement data." />}
        </SectionCard>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Users Tab
// ---------------------------------------------------------------------------

function UsersTab() {
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(false);
  const [page, setPage]         = useState(1);
  const [roleFilter, setRoleFilter]     = useState("");
  const [verifiedFilter, setVerifiedFilter] = useState(""); // "" | "true" | "false"
  const [searchQuery, setSearchQuery]   = useState("");
  const [searchInput, setSearchInput]   = useState("");

  const load = (p = page, rf = roleFilter, vf = verifiedFilter, sq = searchQuery) => {
    setLoading(true);
    setError(false);
    const params = { page: p, page_size: 20 };
    if (rf) params.role = rf;
    if (vf !== "") params.is_verified = vf;
    if (sq) params.search = sq;
    getAdminUsers(params)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(1, roleFilter, verifiedFilter, searchQuery);
    setPage(1);
  }, [roleFilter, verifiedFilter, searchQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(searchInput);
  };

  const clearSearch = () => {
    setSearchInput("");
    setSearchQuery("");
  };

  const handleStatusChange = async (id, newActive, name) => {
    if (!window.confirm(`${newActive ? "Activate" : "Deactivate"} ${name}?`)) return;
    try {
      await updateUserStatus(id, newActive);
      load(page, roleFilter, verifiedFilter, searchQuery);
    } catch {
      alert("Failed to update user status.");
    }
  };

  return (
    <SectionCard title="User Management">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          <input
            type="text"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search by name or email…"
            className="w-full pl-8 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
          {searchInput && (
            <button type="button" onClick={clearSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <XCircle className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <button type="submit"
          className="px-3 py-1.5 bg-brand-600 text-white text-xs font-medium rounded-lg
                     hover:bg-brand-700 transition">
          Search
        </button>
      </form>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="flex gap-1.5">
          {["", "FARMER", "BUYER", "ADMIN"].map(r => (
            <button key={r}
              onClick={() => { setRoleFilter(r); }}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
                roleFilter === r
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
              }`}
            >
              {r || "All roles"}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5 border-l pl-2 ml-1">
          {[["", "All"], ["true", "✓ Verified"], ["false", "Unverified"]].map(([val, label]) => (
            <button key={val}
              onClick={() => setVerifiedFilter(val)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
                verifiedFilter === val
                  ? val === "true"
                    ? "bg-lime-500 text-white border-lime-500"
                    : "bg-gray-500 text-white border-gray-500"
                  : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading && <Loading />}
      {error   && <ErrorMsg onRetry={() => load(page, roleFilter, verifiedFilter, searchQuery)} />}
      {!loading && !error && data && (
        <>
          <p className="text-xs text-gray-400 mb-2">{data.total} user{data.total !== 1 ? "s" : ""} found</p>
          {data.items.length === 0 ? <Empty /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-gray-100">
                    <th className="text-left py-2 pr-3">Name</th>
                    <th className="text-left py-2 pr-3">Email</th>
                    <th className="text-left py-2 pr-3">Role</th>
                    <th className="text-left py-2 pr-3">Verified</th>
                    <th className="text-left py-2 pr-3">Transactions</th>
                    <th className="text-left py-2 pr-3">Status</th>
                    <th className="text-left py-2 pr-3">Joined</th>
                    <th className="text-left py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map(u => (
                    <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-3 font-medium text-gray-900">
                        <div className="flex items-center gap-1.5">
                          {u.full_name}
                          {u.is_verified && (
                            <ShieldCheck
                              className="w-3.5 h-3.5 text-lime-600 shrink-0"
                              title="Verified user"
                              aria-label="Verified"
                            />
                          )}
                        </div>
                      </td>
                      <td className="py-2 pr-3 text-gray-500 text-xs">{u.email}</td>
                      <td className="py-2 pr-3"><Badge status={u.role} /></td>
                      <td className="py-2 pr-3">
                        {u.is_verified ? (
                          <span className="inline-flex items-center gap-1 text-xs text-lime-700 font-medium bg-lime-50 px-2 py-0.5 rounded-full border border-lime-200">
                            <ShieldCheck className="w-3 h-3" /> Verified
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-2 pr-3 text-xs text-gray-600">
                        {u.is_verified
                          ? <span className="text-lime-700 font-medium">5+ completed</span>
                          : <span>{u.completed_transaction_count ?? 0}/5 completed</span>
                        }
                      </td>
                      <td className="py-2 pr-3"><Badge status={u.is_active} /></td>
                      <td className="py-2 pr-3 text-xs text-gray-400">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("en-IN") : "—"}
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => handleStatusChange(u.id, !u.is_active, u.full_name)}
                          className={`flex items-center gap-1 text-xs px-2 py-1 rounded transition ${
                            u.is_active
                              ? "text-red-600 hover:bg-red-50"
                              : "text-brand-600 hover:bg-brand-50"
                          }`}
                        >
                          {u.is_active
                            ? <><ToggleRight className="w-3.5 h-3.5" /> Deactivate</>
                            : <><ToggleLeft  className="w-3.5 h-3.5" /> Activate</>}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Paginator page={page} total={data.total} pageSize={20}
            onChange={p => { setPage(p); load(p, roleFilter, verifiedFilter, searchQuery); }} />
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Farmers Tab
// ---------------------------------------------------------------------------

function FarmersTab() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);
  const [page, setPage]     = useState(1);

  const load = (p = 1) => {
    setLoading(true);
    setError(false);
    getAdminFarmers({ page: p, page_size: 20 })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(1), []);

  return (
    <SectionCard title="Farmer Management">
      {loading && <Loading />}
      {error   && <ErrorMsg onRetry={() => load(page)} />}
      {!loading && !error && data && (
        <>
          {data.items.length === 0 ? <Empty msg="No farmers yet." /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-gray-100">
                    <th className="text-left py-2 pr-3">Name</th>
                    <th className="text-left py-2 pr-3">District</th>
                    <th className="text-left py-2 pr-3">State</th>
                    <th className="text-right py-2 pr-3">Crops</th>
                    <th className="text-right py-2">Available</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map(f => (
                    <tr key={f.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-3 font-medium text-gray-900">{f.full_name}</td>
                      <td className="py-2 pr-3 text-gray-500">{f.district || "—"}</td>
                      <td className="py-2 pr-3 text-gray-500">{f.state || "—"}</td>
                      <td className="py-2 pr-3 text-right text-gray-700">{f.crop_count}</td>
                      <td className="py-2 text-right">
                        <span className={`text-xs font-medium ${f.available_crop_count > 0 ? "text-brand-600" : "text-gray-400"}`}>
                          {f.available_crop_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Paginator page={page} total={data.total} pageSize={20}
            onChange={p => { setPage(p); load(p); }} />
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Buyers Tab
// ---------------------------------------------------------------------------

function BuyersTab() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);
  const [page, setPage]     = useState(1);

  const load = (p = 1) => {
    setLoading(true);
    setError(false);
    getAdminBuyers({ page: p, page_size: 20 })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(1), []);

  return (
    <SectionCard title="Buyer Management">
      {loading && <Loading />}
      {error   && <ErrorMsg onRetry={() => load(page)} />}
      {!loading && !error && data && (
        <>
          {data.items.length === 0 ? <Empty msg="No buyers yet." /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-gray-100">
                    <th className="text-left py-2 pr-3">Name</th>
                    <th className="text-left py-2 pr-3">Business</th>
                    <th className="text-left py-2 pr-3">District</th>
                    <th className="text-left py-2 pr-3">State</th>
                    <th className="text-right py-2">Active Reqs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map(b => (
                    <tr key={b.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-3 font-medium text-gray-900">{b.full_name}</td>
                      <td className="py-2 pr-3 text-gray-500">{b.business_name || "—"}</td>
                      <td className="py-2 pr-3 text-gray-500">{b.district || "—"}</td>
                      <td className="py-2 pr-3 text-gray-500">{b.state || "—"}</td>
                      <td className="py-2 text-right">
                        <span className={`text-xs font-medium ${b.active_requirement_count > 0 ? "text-blue-700" : "text-gray-400"}`}>
                          {b.active_requirement_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Paginator page={page} total={data.total} pageSize={20}
            onChange={p => { setPage(p); load(p); }} />
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Markets Tab
// ---------------------------------------------------------------------------

function MarketsTab() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    getAdminMarkets()
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <SectionCard title="Market Registry">
      {loading && <Loading />}
      {error   && <ErrorMsg onRetry={load} />}
      {!loading && !error && data && (
        data.items.length === 0 ? <Empty msg="No markets yet." /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 border-b border-gray-100">
                  <th className="text-left py-2 pr-3">Name</th>
                  <th className="text-left py-2 pr-3">Type</th>
                  <th className="text-left py-2 pr-3">District</th>
                  <th className="text-left py-2 pr-3">State</th>
                  <th className="text-right py-2 pr-3">Lat</th>
                  <th className="text-right py-2">Lng</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map(m => (
                  <tr key={m.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-3 font-medium text-gray-900">{m.name}</td>
                    <td className="py-2 pr-3 text-xs text-gray-500">{m.market_type || "—"}</td>
                    <td className="py-2 pr-3 text-gray-500">{m.district}</td>
                    <td className="py-2 pr-3 text-gray-500">{m.state}</td>
                    <td className="py-2 pr-3 text-right text-gray-400 text-xs">{m.latitude?.toFixed(4) || "—"}</td>
                    <td className="py-2 text-right text-gray-400 text-xs">{m.longitude?.toFixed(4) || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    getAdminActivity({ limit: 40 })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <SectionCard title="Recent Platform Activity">
      {loading && <Loading />}
      {error   && <ErrorMsg onRetry={load} />}
      {!loading && !error && data && (
        data.items.length === 0 ? <Empty msg="No recent activity." /> : (
          <ul className="divide-y divide-gray-50">
            {data.items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3 py-2.5">
                <Badge status={item.kind} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-800">{item.description}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {item.timestamp ? new Date(item.timestamp).toLocaleString("en-IN") : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )
      )}
    </SectionCard>
  );
}


// ---------------------------------------------------------------------------
// Crop Suggestions Tab (Correction 5)
// ---------------------------------------------------------------------------

function CropSuggestionsTab() {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [filter, setFilter]           = useState("PENDING");
  const [acting, setActing]           = useState({});
  const [msg, setMsg]                 = useState({});

  async function load() {
    setLoading(true);
    try {
      const r = await api.get(`/api/admin/crop-suggestions?status=${filter}`);
      setSuggestions(r.data);
    } catch {}
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [filter]);

  async function review(id, action, adminNotes = "") {
    setActing(a => ({ ...a, [id]: action }));
    try {
      await api.post(`/api/admin/crop-suggestions/${id}/review`, { action, admin_notes: adminNotes || undefined });
      setMsg(m => ({ ...m, [id]: action === "approve" ? "✓ Approved — crop added to catalog" : "✗ Rejected" }));
      load();
    } catch (e) {
      const detail = e.response?.data?.detail;
      setMsg(m => ({ ...m, [id]: typeof detail === "string" ? detail : "Action failed." }));
    } finally {
      setActing(a => ({ ...a, [id]: null }));
    }
  }

  const statusColors = {
    PENDING:  "badge-pending",
    APPROVED: "badge-accepted",
    REJECTED: "badge-rejected",
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold text-neutral-700">Crop Suggestions</p>
        <div className="flex gap-1">
          {["PENDING", "APPROVED", "REJECTED"].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1 text-xs rounded-full border font-medium transition-colors ${
                filter === s
                  ? "bg-brand-600 text-white border-brand-600"
                  : "border-neutral-200 text-neutral-500 hover:border-brand-600 hover:text-brand-600"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <button onClick={load} className="ml-auto text-xs text-neutral-400 hover:text-brand-600">↻ Refresh</button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><div className="spinner" /></div>
      ) : suggestions.length === 0 ? (
        <div className="empty-state">
          <p className="text-sm text-neutral-400">No {filter.toLowerCase()} suggestions.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {suggestions.map(s => (
            <div key={s.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-neutral-900">{s.suggested_name}</span>
                    <span className={statusColors[s.status] || "badge"}>{s.status}</span>
                    {s.approved_crop_id && <span className="text-xs text-brand-600">Crop ID: {s.approved_crop_id}</span>}
                  </div>
                  {s.notes && <p className="text-xs text-neutral-500 italic mb-1">"{s.notes}"</p>}
                  {s.admin_notes && <p className="text-xs text-neutral-400">Admin note: {s.admin_notes}</p>}
                  {msg[s.id] && <p className="text-xs font-medium text-brand-600 mt-1">{msg[s.id]}</p>}
                </div>
                {s.status === "PENDING" && (
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => review(s.id, "approve")}
                      disabled={!!acting[s.id]}
                      className="px-3 py-1.5 bg-brand-600 text-white text-xs rounded-lg hover:bg-brand-700 disabled:opacity-50"
                    >
                      {acting[s.id] === "approve" ? "…" : "Approve"}
                    </button>
                    <button
                      onClick={() => review(s.id, "reject")}
                      disabled={!!acting[s.id]}
                      className="px-3 py-1.5 bg-red-100 text-red-700 text-xs rounded-lg hover:bg-red-200 disabled:opacity-50"
                    >
                      {acting[s.id] === "reject" ? "…" : "Reject"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
