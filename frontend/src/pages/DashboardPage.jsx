import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Leaf, TrendingUp, Users, Lightbulb, BarChart3,
  MapPin, Package, AlertCircle, ArrowRight, RefreshCw,
  ShoppingBag, Clock, CheckCircle2, XCircle,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";
import { useAuth } from "../context/AuthContext";
import { getFarmerDashboard, getBuyerDashboard } from "../services/dashboardService";
import { ROUTES } from "../constants/routes";

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

function StatCard({ icon: Icon, label, value, color = "green", sub }) {
  const colors = {
    green:  "bg-green-50 text-green-700",
    blue:   "bg-blue-50 text-blue-700",
    amber:  "bg-amber-50 text-amber-700",
    purple: "bg-purple-50 text-purple-700",
    rose:   "bg-rose-50 text-rose-700",
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
      <span className={`flex items-center justify-center w-11 h-11 rounded-lg shrink-0 ${colors[color]}`}>
        <Icon className="w-5 h-5" />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <p className="text-xl font-bold text-gray-900 truncate">{value}</p>
        {sub && <p className="text-xs text-gray-400 truncate">{sub}</p>}
      </div>
    </div>
  );
}

function SectionCard({ title, children, action }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function EmptyState({ message, link, linkLabel }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center gap-2">
      <p className="text-sm text-gray-400">{message}</p>
      {link && (
        <Link to={link} className="text-xs font-medium text-green-700 hover:underline flex items-center gap-1">
          {linkLabel} <ArrowRight className="w-3 h-3" />
        </Link>
      )}
    </div>
  );
}

function LoadingSection() {
  return (
    <div className="flex items-center justify-center py-10 text-sm text-gray-400 gap-2">
      <RefreshCw className="w-4 h-4 animate-spin" /> Loading…
    </div>
  );
}

function ErrorSection({ onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-2 text-sm text-red-500">
      <AlertCircle className="w-5 h-5" />
      Unable to load this section.
      {onRetry && (
        <button onClick={onRetry} className="text-xs text-gray-500 hover:underline">Retry</button>
      )}
    </div>
  );
}

const fmt = (n) =>
  n == null ? "—" : `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

// ---------------------------------------------------------------------------
// Farmer Dashboard
// ---------------------------------------------------------------------------

function FarmerDashboard({ user }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    getFarmerDashboard()
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <LoadingSection />;
  if (error)   return <ErrorSection onRetry={load} />;
  if (!data)   return null;

  const { profile, stats, market_snapshot, latest_recommendation,
          buyer_opportunities, recent_activity } = data;

  // Chart data: market snapshot bar chart
  const priceChartData = market_snapshot.slice(0, 6).map((mp) => ({
    name: mp.market_name.replace(" Market", "").replace(" APMC", "").slice(0, 10),
    crop: mp.crop_name,
    price: mp.modal_price,
  }));

  // Activity icons
  const activityIcon = (kind) => {
    if (kind === "recommendation") return <Lightbulb className="w-3.5 h-3.5 text-amber-500" />;
    if (kind === "interest_received") return <Users className="w-3.5 h-3.5 text-blue-500" />;
    return <Clock className="w-3.5 h-3.5 text-gray-400" />;
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Welcome */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {profile.full_name?.split(" ")[0]} 👋
          </h1>
          <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {[profile.village, profile.district, profile.state].filter(Boolean).join(", ") || "Location not set"}
          </p>
        </div>
        {!profile.has_profile && (
          <Link to={ROUTES.PROFILE}
            className="shrink-0 text-xs bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1.5 rounded-lg hover:bg-amber-100">
            Complete your profile
          </Link>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <StatCard icon={Leaf}      label="My Crops"              value={stats.total_crops}            color="green" />
        <StatCard icon={Package}   label="Available for Sale"    value={`${stats.available_crops} crops`}
                  sub={stats.total_available_quantity > 0 ? `${stats.total_available_quantity.toLocaleString()} kg total` : undefined}
                  color="green" />
        <StatCard icon={Users}     label="Buyer Opportunities"   value={stats.buyer_opportunities}    color="blue" />
        <StatCard icon={Lightbulb} label="Recommendations"       value={stats.recommendation_count}  color="amber" />
        <StatCard icon={Clock}     label="Pending Requests"      value={stats.pending_requests}       color="purple" />
        <StatCard icon={CheckCircle2} label="Accepted Connections" value={stats.accepted_requests}    color="green" />
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Latest Recommendation */}
        <SectionCard
          title="Latest Recommendation"
          action={
            <Link to={ROUTES.RECOMMENDATIONS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          }
        >
          {latest_recommendation ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Crop</p>
                  <p className="font-semibold text-gray-900">{latest_recommendation.crop_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Recommended Market</p>
                  <p className="font-semibold text-gray-900">{latest_recommendation.recommended_market}</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-green-50 rounded-lg p-2">
                  <p className="text-xs text-gray-500">Net Revenue</p>
                  <p className="text-sm font-bold text-green-700">{fmt(latest_recommendation.net_revenue)}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-2">
                  <p className="text-xs text-gray-500">Price</p>
                  <p className="text-sm font-bold text-blue-700">{fmt(latest_recommendation.price_used)}/kg</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-2">
                  <p className="text-xs text-gray-500">Transport</p>
                  <p className="text-sm font-bold text-amber-700">{fmt(latest_recommendation.transport_cost)}</p>
                </div>
              </div>
              <p className="text-xs text-gray-400 capitalize">
                Basis: {latest_recommendation.price_basis || "current"} price
              </p>
            </div>
          ) : (
            <EmptyState
              message="No recommendation yet."
              link={ROUTES.RECOMMENDATIONS}
              linkLabel="Get your first recommendation"
            />
          )}
        </SectionCard>

        {/* Market Price Snapshot */}
        <SectionCard
          title="Market Price Snapshot"
          action={
            <Link to={ROUTES.MARKETS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
              View markets <ArrowRight className="w-3 h-3" />
            </Link>
          }
        >
          {priceChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={priceChartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(v) => [`₹${v}/kg`, "Modal Price"]}
                  labelFormatter={(l) => `Market: ${l}`}
                />
                <Bar dataKey="price" fill="#16a34a" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No price data for your crops yet." link={ROUTES.MARKETS} linkLabel="Explore markets" />
          )}
        </SectionCard>
      </div>

      {/* Buyer Opportunities */}
      <SectionCard
        title={`Buyer Opportunities (${stats.buyer_opportunities})`}
        action={
          <Link to={ROUTES.BUYERS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        }
      >
        {buyer_opportunities.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 border-b border-gray-100">
                  <th className="text-left py-1.5 pr-3">Crop</th>
                  <th className="text-right py-1.5 pr-3">Qty (kg)</th>
                  <th className="text-right py-1.5 pr-3">Desired Price</th>
                  <th className="text-left py-1.5">Location</th>
                </tr>
              </thead>
              <tbody>
                {buyer_opportunities.map((opp) => (
                  <tr key={opp.requirement_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-3 font-medium text-gray-900">{opp.crop_name}</td>
                    <td className="py-2 pr-3 text-right text-gray-600">{opp.quantity_kg.toLocaleString()}</td>
                    <td className="py-2 pr-3 text-right text-green-700 font-medium">
                      {opp.desired_price ? `₹${opp.desired_price}/kg` : "—"}
                    </td>
                    <td className="py-2 text-gray-500 text-xs">{opp.location || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No active buyer requirements match your crops yet." link={ROUTES.BUYERS} linkLabel="Browse buyer requirements" />
        )}
      </SectionCard>

      {/* Recent Activity */}
      <SectionCard title="Recent Activity">
        {recent_activity.length > 0 ? (
          <ul className="divide-y divide-gray-50">
            {recent_activity.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3 py-2">
                <span className="mt-0.5">{activityIcon(item.kind)}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-800">{item.description}</p>
                  <p className="text-xs text-gray-400">
                    {item.created_at ? new Date(item.created_at).toLocaleDateString("en-IN") : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState message="No recent activity." />
        )}
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Buyer Dashboard
// ---------------------------------------------------------------------------

function BuyerDashboard({ user }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    getBuyerDashboard()
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <LoadingSection />;
  if (error)   return <ErrorSection onRetry={load} />;
  if (!data)   return null;

  const { profile, stats, active_requirements, matching_farmers, request_activity } = data;

  // Requirement status chart
  const statusData = [
    { name: "Active",    value: stats.active_requirements },
    { name: "Pending",   value: stats.pending_requests },
    { name: "Accepted",  value: stats.accepted_connections },
    { name: "Rejected",  value: stats.rejected_requests },
  ].filter(d => d.value > 0);

  const statusColors = ["#16a34a", "#d97706", "#2563eb", "#dc2626"];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {profile.business_name || profile.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
          <MapPin className="w-3.5 h-3.5" />
          {[profile.location, profile.district, profile.state].filter(Boolean).join(", ") || "Location not set"}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard icon={ShoppingBag}   label="Active Requirements" value={stats.active_requirements}  color="green" />
        <StatCard icon={Users}         label="Matching Farmers"    value={matching_farmers.length}    color="blue" />
        <StatCard icon={Clock}         label="Pending Requests"    value={stats.pending_requests}     color="amber" />
        <StatCard icon={CheckCircle2}  label="Accepted Connections" value={stats.accepted_connections} color="green" />
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Active Requirements */}
        <SectionCard
          title="Active Requirements"
          action={
            <Link to={ROUTES.BUYERS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
              Manage <ArrowRight className="w-3 h-3" />
            </Link>
          }
        >
          {active_requirements.length > 0 ? (
            <ul className="divide-y divide-gray-50">
              {active_requirements.slice(0, 5).map((req) => (
                <li key={req.id} className="py-2.5 flex items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{req.crop_name}</p>
                    <p className="text-xs text-gray-500">
                      {req.quantity_kg.toLocaleString()} kg
                      {req.desired_price ? ` · ₹${req.desired_price}/kg` : ""}
                      {req.location ? ` · ${req.location}` : ""}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
                    {req.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState message="No active requirements." link={ROUTES.BUYERS} linkLabel="Post a requirement" />
          )}
        </SectionCard>

        {/* Activity / Status chart */}
        <SectionCard title="Activity Summary">
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={statusData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {statusData.map((_, i) => (
                    <rect key={i} fill={statusColors[i % statusColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No activity data yet." />
          )}
        </SectionCard>
      </div>

      {/* Matching Farmers */}
      <SectionCard
        title={`Matching Farmers (${matching_farmers.length})`}
        action={
          <Link to={ROUTES.BUYERS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
            Find farmers <ArrowRight className="w-3 h-3" />
          </Link>
        }
      >
        {matching_farmers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 border-b border-gray-100">
                  <th className="text-left py-1.5 pr-3">Farmer</th>
                  <th className="text-left py-1.5 pr-3">Crop</th>
                  <th className="text-right py-1.5 pr-3">Available (kg)</th>
                  <th className="text-left py-1.5">Location</th>
                </tr>
              </thead>
              <tbody>
                {matching_farmers.map((f) => (
                  <tr key={f.farmer_crop_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-3 font-medium text-gray-900">{f.farmer_name}</td>
                    <td className="py-2 pr-3 text-gray-600">{f.crop_name}</td>
                    <td className="py-2 pr-3 text-right text-green-700">{f.available_quantity.toLocaleString()}</td>
                    <td className="py-2 text-gray-500 text-xs">{f.location || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No matching farmers found for your active requirements." link={ROUTES.BUYERS} linkLabel="Post requirements to find matches" />
        )}
      </SectionCard>

      {/* Request Activity */}
      <SectionCard
        title="Request Activity"
        action={
          <Link to={ROUTES.BUYERS} className="text-xs text-green-700 hover:underline flex items-center gap-0.5">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        }
      >
        {request_activity.length > 0 ? (
          <ul className="divide-y divide-gray-50">
            {request_activity.map((item) => {
              const isAccepted = item.status === "ACCEPTED";
              const isRejected = item.status === "REJECTED";
              return (
                <li key={item.id} className="flex items-center gap-3 py-2.5">
                  <span>
                    {isAccepted ? <CheckCircle2 className="w-4 h-4 text-green-500" /> :
                     isRejected ? <XCircle className="w-4 h-4 text-red-400" /> :
                                  <Clock className="w-4 h-4 text-amber-400" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-800">
                      {item.crop_name ? `${item.crop_name}` : "Interest"} with {item.other_party || "Farmer"}
                    </p>
                    <p className="text-xs text-gray-400">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString("en-IN") : ""}
                    </p>
                  </div>
                  <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium
                    ${isAccepted ? "bg-green-50 text-green-700" :
                      isRejected ? "bg-red-50 text-red-600" :
                                   "bg-amber-50 text-amber-700"}`}>
                    {item.status}
                  </span>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState message="No requests sent yet." link={ROUTES.BUYERS} linkLabel="Find farmers" />
        )}
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root: role-aware router
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  if (user.role === "BUYER") return <BuyerDashboard user={user} />;
  return <FarmerDashboard user={user} />;
}
