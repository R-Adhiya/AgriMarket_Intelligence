import { useEffect, useState } from "react";
import { User, MapPin, Leaf, Save, Plus, Trash2, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import {
  getFarmerProfile, updateFarmerProfile,
  getFarmerCrops, addFarmerCrop, deleteFarmerCrop,
} from "../services/farmerService";
import api from "../services/api";
import PageHeader from "../components/PageHeader";

const UNITS = ["kg", "quintal", "ton"];

export default function ProfilePage() {
  const { user } = useAuth();
  const isFarmer = user?.role === "FARMER";

  // ── Profile state ─────────────────────────────────────────────────────────
  const [profile, setProfile]     = useState({ village: "", district: "", state: "", farm_size: "" });
  const [profileSaving, setPS]    = useState(false);
  const [profileMsg, setPM]       = useState(null); // {type:"ok"|"err", text}

  // ── Crops state ───────────────────────────────────────────────────────────
  const [crops, setCrops]           = useState([]);
  const [allCrops, setAllCrops]     = useState([]);
  const [newCrop, setNewCrop]       = useState({ crop_id: "", quantity: "", unit: "quintal" });
  const [cropError, setCropError]   = useState("");
  const [cropAdding, setCropAdding] = useState(false);

  // Load on mount
  useEffect(() => {
    if (!isFarmer) return;
    getFarmerProfile()
      .then((p) => setProfile({
        village: p.village || "", district: p.district || "",
        state: p.state || "", farm_size: p.farm_size ?? "",
      }))
      .catch(() => {});
    getFarmerCrops().then(setCrops).catch(() => {});
    // Load crop catalogue via the axios instance (no raw fetch)
    api.get("/api/crops")
      .then((r) => setAllCrops(r.data))
      .catch(() => setAllCrops([]));
  }, [isFarmer]);

  // ── Profile save ──────────────────────────────────────────────────────────
  async function saveProfile(e) {
    e.preventDefault();
    setPS(true);
    setPM(null);
    try {
      const payload = {};
      if (profile.village)    payload.village   = profile.village;
      if (profile.district)   payload.district  = profile.district;
      if (profile.state)      payload.state     = profile.state;
      if (profile.farm_size !== "") payload.farm_size = parseFloat(profile.farm_size);
      await updateFarmerProfile(payload);
      setPM({ type: "ok", text: "Profile saved successfully." });
    } catch {
      setPM({ type: "err", text: "Failed to save profile. Please try again." });
    } finally {
      setPS(false);
    }
  }

  // ── Add crop ──────────────────────────────────────────────────────────────
  async function handleAddCrop(e) {
    e.preventDefault();
    setCropError("");
    if (!newCrop.crop_id) { setCropError("Please select a crop."); return; }
    const qty = parseFloat(newCrop.quantity);
    if (!qty || qty <= 0) { setCropError("Quantity must be greater than 0."); return; }
    setCropAdding(true);
    try {
      const entry = await addFarmerCrop({
        crop_id: parseInt(newCrop.crop_id), quantity: qty, unit: newCrop.unit,
      });
      setCrops((prev) => [entry, ...prev]);
      setNewCrop({ crop_id: "", quantity: "", unit: "quintal" });
    } catch (err) {
      setCropError(err.response?.data?.detail || "Failed to add crop. Please try again.");
    } finally {
      setCropAdding(false);
    }
  }

  async function handleDeleteCrop(id) {
    try {
      await deleteFarmerCrop(id);
      setCrops((prev) => prev.filter((c) => c.id !== id));
    } catch {
      // deletion errors are non-critical
    }
  }

  if (!isFarmer) {
    return (
      <div className="p-6 sm:p-8 max-w-2xl mx-auto">
        <PageHeader icon={User} title="My Profile" />
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <User className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">
            Detailed profile management for your account type will be available soon.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 sm:p-8 max-w-3xl mx-auto space-y-5">
      <PageHeader icon={User} title="My Profile" subtitle="Manage your farm details and crop listings" />

      {/* ── Account info (read-only) ── */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm mb-4 pb-3 border-b border-gray-100">
          <User className="w-4 h-4 text-green-700" aria-hidden="true" />
          Account Information
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <InfoRow label="Full Name" value={user?.full_name} />
          <InfoRow label="Email Address" value={user?.email} />
          {user?.phone && <InfoRow label="Phone" value={user.phone} />}
          <InfoRow label="Account Type" value={user?.role?.charAt(0) + user?.role?.slice(1).toLowerCase()} />
        </dl>
      </div>

      {/* ── Location & farm ── */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm mb-4 pb-3 border-b border-gray-100">
          <MapPin className="w-4 h-4 text-green-700" aria-hidden="true" />
          Location &amp; Farm Details
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField
              label="Village / City"
              value={profile.village}
              onChange={(v) => setProfile((p) => ({ ...p, village: v }))}
              placeholder="e.g. Coimbatore"
            />
            <FormField
              label="District"
              value={profile.district}
              onChange={(v) => setProfile((p) => ({ ...p, district: v }))}
              placeholder="e.g. Coimbatore"
              required
              hint="Required for recommendations and transport estimates"
            />
            <FormField
              label="State"
              value={profile.state}
              onChange={(v) => setProfile((p) => ({ ...p, state: v }))}
              placeholder="e.g. Tamil Nadu"
            />
            <FormField
              label="Farm Size (acres)"
              value={profile.farm_size}
              onChange={(v) => setProfile((p) => ({ ...p, farm_size: v }))}
              placeholder="e.g. 2.5"
              type="number"
            />
          </div>

          {profileMsg && (
            <div className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2.5
              ${profileMsg.type === "ok" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
              {profileMsg.type === "ok"
                ? <CheckCircle className="w-4 h-4 shrink-0" />
                : <AlertCircle className="w-4 h-4 shrink-0" />}
              {profileMsg.text}
            </div>
          )}

          <button
            type="submit"
            disabled={profileSaving}
            className="inline-flex items-center gap-2 bg-green-700 hover:bg-green-800
                       disabled:bg-green-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Save className="w-3.5 h-3.5" aria-hidden="true" />
            {profileSaving ? "Saving…" : "Save location details"}
          </button>
        </form>
      </div>

      {/* ── Crops ── */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm mb-4 pb-3 border-b border-gray-100">
          <Leaf className="w-4 h-4 text-green-700" aria-hidden="true" />
          My Crop Listings
        </div>

        {/* Add crop form */}
        <form onSubmit={handleAddCrop} className="flex flex-wrap gap-2 items-end mb-4 pb-4 border-b border-gray-100">
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-600 mb-1" htmlFor="crop-select">
              Crop
            </label>
            {allCrops.length > 0 ? (
              <select
                id="crop-select"
                value={newCrop.crop_id}
                onChange={(e) => setNewCrop((p) => ({ ...p, crop_id: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
              >
                <option value="">Select crop…</option>
                {allCrops.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            ) : (
              <input
                id="crop-select"
                type="number"
                min="1"
                placeholder="Crop ID"
                value={newCrop.crop_id}
                onChange={(e) => setNewCrop((p) => ({ ...p, crop_id: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            )}
          </div>
          <div className="w-28">
            <label className="block text-xs font-medium text-gray-600 mb-1" htmlFor="crop-qty">
              Quantity
            </label>
            <input
              id="crop-qty"
              type="number"
              min="0.001"
              step="any"
              placeholder="e.g. 50"
              value={newCrop.quantity}
              onChange={(e) => setNewCrop((p) => ({ ...p, quantity: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="w-28">
            <label className="block text-xs font-medium text-gray-600 mb-1" htmlFor="crop-unit">
              Unit
            </label>
            <select
              id="crop-unit"
              value={newCrop.unit}
              onChange={(e) => setNewCrop((p) => ({ ...p, unit: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <button
            type="submit"
            disabled={cropAdding}
            className="inline-flex items-center gap-1.5 bg-green-700 hover:bg-green-800
                       disabled:bg-green-400 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" />
            {cropAdding ? "Adding…" : "Add crop"}
          </button>
        </form>

        {cropError && (
          <div className="mb-3 flex items-center gap-1.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {cropError}
          </div>
        )}

        {/* Crop list */}
        {crops.length === 0 ? (
          <div className="text-center py-8">
            <Leaf className="w-8 h-8 text-gray-200 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No crops added yet.</p>
            <p className="text-xs text-gray-400 mt-1">Add your first crop using the form above.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {crops.map((c) => (
              <div key={c.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center shrink-0">
                    <Leaf className="w-4 h-4 text-green-600" aria-hidden="true" />
                  </span>
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{c.crop?.name || `Crop #${c.crop_id}`}</p>
                    <p className="text-xs text-gray-500">
                      {c.quantity} {c.unit}
                      {c.notes && <span className="ml-2 italic text-gray-400">{c.notes}</span>}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCrop(c.id)}
                  className="text-gray-300 hover:text-red-500 transition-colors p-1.5 rounded-lg hover:bg-red-50"
                  aria-label={`Remove ${c.crop?.name || "crop"}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Shared sub-components ─────────────────────────────────────────────────────

function InfoRow({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-0.5">{label}</dt>
      <dd className="text-sm font-medium text-gray-800">{value || <span className="text-gray-400 italic">Not set</span>}</dd>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder, type = "text", required, hint }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                   focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
      />
      {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
    </div>
  );
}
