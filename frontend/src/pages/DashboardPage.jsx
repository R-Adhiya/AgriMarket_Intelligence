import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { User, Leaf, MapPin, Package, Plus, AlertCircle, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getFarmerProfile, getFarmerCrops } from "../services/farmerService";

export default function DashboardPage() {
  const { user } = useAuth();
  const isFarmer = user?.role === "FARMER";

  const [profile, setProfile] = useState(null);
  const [crops, setCrops]     = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  useEffect(() => {
    if (!isFarmer) return;
    setLoading(true);
    Promise.all([getFarmerProfile(), getFarmerCrops()])
      .then(([p, c]) => { setProfile(p); setCrops(c); })
      .catch(() => setError("Could not load farmer data."))
      .finally(() => setLoading(false));
  }, [isFarmer]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {isFarmer ? "Farmer Dashboard" : `${user?.role?.charAt(0)}${user?.role?.slice(1).toLowerCase()} Dashboard`}
          &nbsp;— Phase data available after full setup
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {loading && (
        <div className="text-sm text-gray-400 mb-4">Loading…</div>
      )}

      {/* Farmer content */}
      {isFarmer && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Profile card */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm">
                <User size={16} /> Profile
              </div>
              <Link to="/profile" className="text-xs text-green-700 hover:underline flex items-center gap-1">
                Edit <ArrowRight size={12} />
              </Link>
            </div>
            {profile ? (
              <dl className="space-y-1 text-sm">
                <Row label="Name"  value={profile.full_name} />
                <Row label="Email" value={profile.email} />
                {profile.phone && <Row label="Phone" value={profile.phone} />}
              </dl>
            ) : (
              <p className="text-sm text-gray-400">No profile data yet.</p>
            )}
          </div>

          {/* Location card */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm">
                <MapPin size={16} /> Location
              </div>
              <Link to="/profile" className="text-xs text-green-700 hover:underline flex items-center gap-1">
                Edit <ArrowRight size={12} />
              </Link>
            </div>
            {profile?.village || profile?.district || profile?.state ? (
              <dl className="space-y-1 text-sm">
                {profile.village  && <Row label="Village"  value={profile.village} />}
                {profile.district && <Row label="District" value={profile.district} />}
                {profile.state    && <Row label="State"    value={profile.state} />}
                {profile.farm_size != null && (
                  <Row label="Farm size" value={`${profile.farm_size} acres`} />
                )}
              </dl>
            ) : (
              <p className="text-sm text-gray-400">
                Location not set.{" "}
                <Link to="/profile" className="text-green-700 hover:underline">Add it</Link>
              </p>
            )}
          </div>

          {/* Crops summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 md:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm">
                <Leaf size={16} /> My Crops
              </div>
              <Link to="/markets" className="text-xs text-green-700 hover:underline flex items-center gap-1">
                Manage <ArrowRight size={12} />
              </Link>
            </div>

            {crops.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-gray-400 text-sm gap-2">
                <Package size={28} className="text-gray-300" />
                <span>No crops added yet.</span>
                <Link to="/markets" className="text-green-700 hover:underline flex items-center gap-1 text-xs">
                  <Plus size={12} /> Add your first crop
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b border-gray-100">
                      <th className="pb-2 font-medium">Crop</th>
                      <th className="pb-2 font-medium">Quantity</th>
                      <th className="pb-2 font-medium">Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {crops.map((c) => (
                      <tr key={c.id} className="border-b border-gray-50 last:border-0">
                        <td className="py-2 font-medium text-gray-800">{c.crop.name}</td>
                        <td className="py-2 text-gray-600">{c.quantity}</td>
                        <td className="py-2 text-gray-500">{c.unit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Placeholder metric cards */}
          {[
            { label: "Current Market Price", value: "—", note: "Available in Phase 5" },
            { label: "Predicted Price",       value: "—", note: "Available in Phase 6" },
            { label: "Best Market",           value: "—", note: "Available in Phase 5" },
            { label: "Expected Net Return",   value: "—", note: "Available in Phase 6" },
          ].map((m) => (
            <div key={m.label} className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs text-gray-400 mb-1">{m.label}</p>
              <p className="text-2xl font-bold text-gray-300">{m.value}</p>
              <p className="text-xs text-gray-300 mt-1">{m.note}</p>
            </div>
          ))}
        </div>
      )}

      {/* Non-farmer placeholder */}
      {!isFarmer && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
          <p className="text-sm">Dashboard functionality for your role is coming in a later phase.</p>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-gray-400 shrink-0">{label}</dt>
      <dd className="text-gray-800 font-medium text-right truncate">{value}</dd>
    </div>
  );
}
