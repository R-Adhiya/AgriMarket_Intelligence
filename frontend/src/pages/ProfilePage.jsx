import { useEffect, useState } from "react";
import { User, MapPin, Leaf, Save, Plus, Trash2, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import {
  getFarmerProfile, updateFarmerProfile,
  getFarmerCrops, addFarmerCrop, updateFarmerCrop, deleteFarmerCrop,
} from "../services/farmerService";
import api from "../services/api";

const UNITS = ["kg", "quintal", "ton"];

export default function ProfilePage() {
  const { user } = useAuth();
  const isFarmer = user?.role === "FARMER";

  // ── Profile state ─────────────────────────────────────────────────────────
  const [profile, setProfile] = useState({ village: "", district: "", state: "", farm_size: "" });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg]       = useState(null); // {type, text}

  // ── Crops state ───────────────────────────────────────────────────────────
  const [crops, setCrops]         = useState([]);
  const [allCrops, setAllCrops]   = useState([]);  // catalogue
  const [newCrop, setNewCrop]     = useState({ crop_id: "", quantity: "", unit: "quintal" });
  const [cropError, setCropError] = useState("");
  const [cropAdding, setCropAdding] = useState(false);

  // Load on mount
  useEffect(() => {
    if (!isFarmer) return;
    getFarmerProfile().then((p) =>
      setProfile({ village: p.village || "", district: p.district || "", state: p.state || "", farm_size: p.farm_size ?? "" })
    ).catch(() => {});
    getFarmerCrops().then(setCrops).catch(() => {});
    // Load crop catalogue
    api.get("/api/health").then(() => {})  // warm-up
    fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/farmer/crops`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("agrimarket_access_token")}` }
    }).catch(() => {});
    // We'll let the user type a crop name and look it up when adding
  }, [isFarmer]);

  // Load available crops for the dropdown
  useEffect(() => {
    if (!isFarmer) return;
    api.get("/api/farmer/crops").catch(() => {});
    // Fetch crop catalogue via a simple direct call
    const token = localStorage.getItem("agrimarket_access_token");
    fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/crops`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.ok ? r.json() : [])
      .then(setAllCrops)
      .catch(() => setAllCrops([]));
  }, [isFarmer]);

  // ── Profile save ──────────────────────────────────────────────────────────
  async function saveProfile(e) {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      const payload = {};
      if (profile.village)   payload.village  = profile.village;
      if (profile.district)  payload.district = profile.district;
      if (profile.state)     payload.state    = profile.state;
      if (profile.farm_size) payload.farm_size = parseFloat(profile.farm_size);
      await updateFarmerProfile(payload);
      setProfileMsg({ type: "ok", text: "Profile saved." });
    } catch {
      setProfileMsg({ type: "err", text: "Failed to save profile." });
    } finally {
      setProfileSaving(false);
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
      const entry = await addFarmerCrop({ crop_id: parseInt(newCrop.crop_id), quantity: qty, unit: newCrop.unit });
      setCrops((prev) => [entry, ...prev]);
      setNewCrop({ crop_id: "", quantity: "", unit: "quintal" });
    } catch (err) {
      setCropError(err.response?.data?.detail || "Failed to add crop.");
    } finally {
      setCropAdding(false);
    }
  }

  async function handleDeleteCrop(id) {
    await deleteFarmerCrop(id);
    setCrops((prev) => prev.filter((c) => c.id !== id));
  }

  if (!isFarmer) {
    return (
      <div className="p-6 max-w-2xl mx-auto text-center text-gray-500 mt-12">
        <p>Profile management for your role is coming in a later phase.</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>

      {/* ── Identity (read-only from auth) ── */}
      <Section icon={<User size={16} />} title="Account">
        <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <Row label="Name"  value={user?.full_name} />
          <Row label="Email" value={user?.email} />
          {user?.phone && <Row label="Phone" value={user.phone} />}
          <Row label="Role"  value={user?.role?.charAt(0) + user?.role?.slice(1).toLowerCase()} />
        </dl>
      </Section>

      {/* ── Location & farm ── */}
      <Section icon={<MapPin size={16} />} title="Location & Farm">
        <form onSubmit={saveProfile} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Village / City" value={profile.village}   onChange={(v) => setProfile((p) => ({ ...p, village: v }))}   placeholder="Coimbatore" />
            <Field label="District"       value={profile.district}  onChange={(v) => setProfile((p) => ({ ...p, district: v }))}  placeholder="Coimbatore" />
            <Field label="State"          value={profile.state}     onChange={(v) => setProfile((p) => ({ ...p, state: v }))}     placeholder="Tamil Nadu" />
            <Field label="Farm size (acres)" value={profile.farm_size} onChange={(v) => setProfile((p) => ({ ...p, farm_size: v }))} placeholder="e.g. 2.5" type="number" />
          </div>
          {profileMsg && (
            <div className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${profileMsg.type === "ok" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
              {profileMsg.type === "ok" ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
              {profileMsg.text}
            </div>
          )}
          <button
            type="submit"
            disabled={profileSaving}
            className="flex items-center gap-2 bg-green-700 hover:bg-green-800 disabled:bg-green-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
          >
            <Save size={14} />
            {profileSaving ? "Saving…" : "Save location"}
          </button>
        </form>
      </Section>

      {/* ── Crops ── */}
      <Section icon={<Leaf size={16} />} title="My Crops">
        {/* Add crop form */}
        <form onSubmit={handleAddCrop} className="flex flex-wrap gap-2 items-end mb-4">
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs text-gray-500 mb-1">Crop ID</label>
            <input
              type="number"
              min="1"
              placeholder="Crop ID (from seed data)"
              value={newCrop.crop_id}
              onChange={(e) => setNewCrop((p) => ({ ...p, crop_id: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="w-28">
            <label className="block text-xs text-gray-500 mb-1">Quantity</label>
            <input
              type="number"
              min="0.001"
              step="any"
              placeholder="e.g. 50"
              value={newCrop.quantity}
              onChange={(e) => setNewCrop((p) => ({ ...p, quantity: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="w-28">
            <label className="block text-xs text-gray-500 mb-1">Unit</label>
            <select
              value={newCrop.unit}
              onChange={(e) => setNewCrop((p) => ({ ...p, unit: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <button
            type="submit"
            disabled={cropAdding}
            className="flex items-center gap-1 bg-green-700 hover:bg-green-800 disabled:bg-green-400 text-white text-sm font-medium px-3 py-2 rounded-lg transition self-end"
          >
            <Plus size={14} /> {cropAdding ? "Adding…" : "Add"}
          </button>
        </form>
        {cropError && (
          <p className="text-xs text-red-600 mb-3 flex items-center gap-1"><AlertCircle size={12} />{cropError}</p>
        )}

        {/* Crop list */}
        {crops.length === 0 ? (
          <p className="text-sm text-gray-400">No crops added yet.</p>
        ) : (
          <div className="space-y-2">
            {crops.map((c) => (
              <div key={c.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2.5">
                <div>
                  <span className="font-medium text-gray-800 text-sm">{c.crop.name}</span>
                  <span className="text-gray-500 text-xs ml-2">{c.quantity} {c.unit}</span>
                  {c.notes && <span className="text-gray-400 text-xs ml-2 italic">{c.notes}</span>}
                </div>
                <button
                  onClick={() => handleDeleteCrop(c.id)}
                  className="text-gray-400 hover:text-red-500 transition p-1 rounded"
                  aria-label="Delete crop"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

// ── Small components ──────────────────────────────────────────────────────────

function Section({ icon, title, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm mb-4">
        {icon} {title}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <>
      <dt className="text-gray-400">{label}</dt>
      <dd className="text-gray-800 font-medium">{value}</dd>
    </>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
      />
    </div>
  );
}
