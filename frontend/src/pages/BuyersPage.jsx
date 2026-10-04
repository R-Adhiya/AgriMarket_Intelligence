/**
 * BuyersPage — Phase 9: Direct Buyer-Farmer Market Access
 *
 * Tabs:
 *   For BUYER role:
 *     Dashboard | My Requirements | Find Farmers | Requests
 *   For FARMER role:
 *     Buyer Requirements | Received Requests
 */
import { useState, useEffect, useCallback } from "react";
import { Users, ShoppingCart, Search, MessageSquare, Plus, CheckCircle, XCircle, Clock } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import StatusBadge from "../components/StatusBadge";
import PageHeader from "../components/PageHeader";

// ── helpers ───────────────────────────────────────────────────────────────────
const fmt = (n) => n != null ? `₹${Number(n).toLocaleString("en-IN")}` : "—";
const fmtQty = (n, unit = "kg") => n != null ? `${Number(n).toLocaleString("en-IN")} ${unit}` : "—";

// Use the shared StatusBadge (aliased locally for backward compat with existing JSX in this file)
const Badge = ({ status }) => <StatusBadge status={status} />;

function SectionTitle({ children }) {
  return <h2 className="text-base font-semibold text-gray-800 mb-3">{children}</h2>;
}

function EmptyState({ message }) {
  return <p className="text-sm text-gray-400 py-6 text-center">{message}</p>;
}

// ── Buyer Profile Summary ──────────────────────────────────────────────────────
function BuyerProfileCard({ profile, onRefresh }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (profile) setForm({
      business_name: profile.business_name || "",
      phone: profile.phone || "",
      location: profile.location || "",
      district: profile.district || "",
      state: profile.state || "",
    });
  }, [profile]);

  async function save() {
    setSaving(true); setErr("");
    try {
      await api.put("/api/buyer/profile", form);
      setEditing(false);
      onRefresh();
    } catch (e) {
      setErr(e.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  }

  if (!profile) return <p className="text-sm text-gray-400">Loading profile…</p>;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm uppercase">
            {(profile.full_name || profile.email || "B")[0]}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{profile.full_name || profile.email}</p>
            <p className="text-xs text-gray-400">Buyer · {profile.email}</p>
          </div>
        </div>
        <button onClick={() => setEditing(!editing)} className="text-xs text-blue-600 hover:underline">
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      {editing ? (
        <div className="space-y-2">
          {[
            ["business_name","Business name"],
            ["phone","Phone"],
            ["location","Location"],
            ["district","District"],
            ["state","State"],
          ].map(([k, label]) => (
            <div key={k}>
              <label className="text-xs text-gray-500">{label}</label>
              <input
                className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={form[k]}
                onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
              />
            </div>
          ))}
          {err && <p className="text-xs text-red-500">{err}</p>}
          <button
            onClick={save} disabled={saving}
            className="mt-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-600">
          {profile.business_name && <><span className="text-gray-400">Business</span><span>{profile.business_name}</span></>}
          {profile.phone        && <><span className="text-gray-400">Phone</span><span>{profile.phone}</span></>}
          {profile.location     && <><span className="text-gray-400">Location</span><span>{profile.location}</span></>}
          {profile.district     && <><span className="text-gray-400">District</span><span>{profile.district}</span></>}
          {profile.state        && <><span className="text-gray-400">State</span><span>{profile.state}</span></>}
        </div>
      )}
    </div>
  );
}

// ── Buyer: My Requirements ─────────────────────────────────────────────────────
function MyRequirements({ crops }) {
  const [reqs, setReqs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ crop_id: "", quantity: "", minimum_price: "", maximum_price: "", location: "", district: "", state: "", description: "" });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    try { const r = await api.get("/api/buyer/requirements"); setReqs(r.data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function createReq() {
    if (!form.crop_id) { setErr("Select a crop"); return; }
    setSaving(true); setErr("");
    try {
      await api.post("/api/buyer/requirements", {
        crop_id: parseInt(form.crop_id),
        quantity: form.quantity ? parseFloat(form.quantity) : null,
        minimum_price: form.minimum_price ? parseFloat(form.minimum_price) : null,
        maximum_price: form.maximum_price ? parseFloat(form.maximum_price) : null,
        location: form.location || null,
        district: form.district || null,
        state: form.state || null,
        description: form.description || null,
      });
      setShowForm(false);
      setForm({ crop_id: "", quantity: "", minimum_price: "", maximum_price: "", location: "", district: "", state: "", description: "" });
      load();
    } catch (e) {
      setErr(e.response?.data?.detail || "Failed to create requirement");
    } finally { setSaving(false); }
  }

  async function deleteReq(id) {
    if (!window.confirm("Delete this requirement?")) return;
    try { await api.delete(`/api/buyer/requirements/${id}`); load(); } catch {}
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <SectionTitle>My Requirements</SectionTitle>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
          <Plus size={13} /> New Requirement
        </button>
      </div>

      {showForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">Post a Purchase Requirement</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-gray-500">Crop *</label>
              <select className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" value={form.crop_id} onChange={e => setForm(f => ({ ...f, crop_id: e.target.value }))}>
                <option value="">Select crop</option>
                {crops.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500">Quantity (kg)</label>
              <input type="number" className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" placeholder="e.g. 500" value={form.quantity} onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Min price (₹/kg)</label>
              <input type="number" className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" placeholder="e.g. 25" value={form.minimum_price} onChange={e => setForm(f => ({ ...f, minimum_price: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Max price (₹/kg)</label>
              <input type="number" className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" placeholder="e.g. 35" value={form.maximum_price} onChange={e => setForm(f => ({ ...f, maximum_price: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Location</label>
              <input className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" placeholder="e.g. Coimbatore" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">District</label>
              <input className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" value={form.district} onChange={e => setForm(f => ({ ...f, district: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">State</label>
              <input className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded" value={form.state} onChange={e => setForm(f => ({ ...f, state: e.target.value }))} />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500">Notes / description</label>
              <textarea rows={2} className="w-full mt-0.5 px-2 py-1.5 text-sm border border-gray-300 rounded resize-none" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
            </div>
          </div>
          {err && <p className="text-xs text-red-500 mt-1">{err}</p>}
          <div className="flex gap-2 mt-3">
            <button onClick={createReq} disabled={saving} className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50">{saving ? "Saving…" : "Post Requirement"}</button>
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-xs text-gray-600 hover:underline">Cancel</button>
          </div>
        </div>
      )}

      {reqs.length === 0 ? <EmptyState message="No requirements posted yet." /> : (
        <div className="space-y-2">
          {reqs.map(r => (
            <div key={r.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-semibold text-gray-800">{r.crop_name}</span>
                  <span className="ml-2"><Badge status={r.status} /></span>
                </div>
                <button onClick={() => deleteReq(r.id)} className="text-xs text-red-500 hover:underline">Delete</button>
              </div>
              <div className="mt-1.5 text-xs text-gray-500 space-x-3">
                {r.quantity && <span>Qty: {fmtQty(r.quantity)}</span>}
                {r.minimum_price && <span>Min: {fmt(r.minimum_price)}/kg</span>}
                {r.maximum_price && <span>Max: {fmt(r.maximum_price)}/kg</span>}
                {r.location && <span>📍 {r.location}{r.district ? `, ${r.district}` : ""}{r.state ? `, ${r.state}` : ""}</span>}
              </div>
              {r.description && <p className="mt-1 text-xs text-gray-400 italic">{r.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Buyer: Find Farmers ────────────────────────────────────────────────────────
function FindFarmers() {
  const [reqs, setReqs] = useState([]);
  const [selectedReq, setSelectedReq] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [sending, setSending] = useState({});
  const [msg, setMsg] = useState({});

  useEffect(() => {
    api.get("/api/buyer/requirements").then(r => setReqs(r.data.filter(x => x.status === "ACTIVE"))).catch(() => {});
  }, []);

  async function loadMatches(req) {
    setSelectedReq(req);
    setLoadingMatches(true);
    setMatches([]);
    try {
      const r = await api.get(`/api/buyer/matches/${req.id}`);
      setMatches(r.data);
    } catch { setMatches([]); }
    finally { setLoadingMatches(false); }
  }

  async function sendInterest(farmerId, farmerCropId) {
    if (!selectedReq) return;
    setSending(s => ({ ...s, [farmerId]: true }));
    try {
      await api.post("/api/interests", {
        farmer_id: farmerId,
        farmer_crop_id: farmerCropId,
        requirement_id: selectedReq.id,
        notes: `Interested in your ${selectedReq.crop_name} supply.`,
      });
      setMsg(m => ({ ...m, [farmerId]: "Request sent!" }));
    } catch (e) {
      const detail = e.response?.data?.detail;
      setMsg(m => ({ ...m, [farmerId]: typeof detail === "string" ? detail : "Already sent or error." }));
    } finally { setSending(s => ({ ...s, [farmerId]: false })); }
  }

  return (
    <div>
      <SectionTitle>Find Farmers</SectionTitle>
      {reqs.length === 0 ? (
        <p className="text-sm text-gray-400">Post an active requirement first to find matching farmers.</p>
      ) : (
        <div className="mb-4">
          <label className="text-xs text-gray-500">Select your requirement</label>
          <select
            className="mt-1 w-full px-2 py-2 text-sm border border-gray-300 rounded"
            value={selectedReq?.id || ""}
            onChange={e => {
              const r = reqs.find(x => x.id === parseInt(e.target.value));
              if (r) loadMatches(r);
            }}
          >
            <option value="">— choose —</option>
            {reqs.map(r => <option key={r.id} value={r.id}>{r.crop_name} · {fmtQty(r.quantity)}</option>)}
          </select>
        </div>
      )}

      {selectedReq && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-4 text-xs text-gray-600">
          <span className="font-semibold text-gray-700">{selectedReq.crop_name}</span>
          {selectedReq.quantity && <> · Required: {fmtQty(selectedReq.quantity)}</>}
          {selectedReq.maximum_price && <> · Desired price: up to {fmt(selectedReq.maximum_price)}/kg</>}
        </div>
      )}

      {loadingMatches && <p className="text-sm text-gray-400">Searching for matching farmers…</p>}

      {!loadingMatches && selectedReq && matches.length === 0 && (
        <EmptyState message="No matching farmers found for this requirement." />
      )}

      {matches.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 mb-2">{matches.length} matching farmer{matches.length !== 1 ? "s" : ""} found</p>
          {matches.map(m => (
            <div key={m.farmer_id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-800">{m.farmer_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {m.crop} · Available: {fmtQty(m.available_quantity)}
                    {m.location && <> · 📍 {m.location}</>}
                  </p>
                </div>
                <button
                  onClick={() => sendInterest(m.farmer_id, m.farmer_crop_id)}
                  disabled={sending[m.farmer_id]}
                  className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
                >
                  {sending[m.farmer_id] ? "Sending…" : "Send Interest"}
                </button>
              </div>
              {msg[m.farmer_id] && (
                <p className={`mt-1.5 text-xs ${msg[m.farmer_id].includes("sent") ? "text-green-600" : "text-amber-600"}`}>
                  {msg[m.farmer_id]}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Buyer: Sent Requests ───────────────────────────────────────────────────────
function SentRequests() {
  const [interests, setInterests] = useState([]);

  const load = useCallback(async () => {
    try { const r = await api.get("/api/interests/sent"); setInterests(r.data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function cancel(id) {
    try { await api.delete(`/api/interests/${id}`); load(); } catch {}
  }

  return (
    <div>
      <SectionTitle>Sent Requests</SectionTitle>
      {interests.length === 0 ? <EmptyState message="No interest requests sent yet." /> : (
        <div className="space-y-2">
          {interests.map(i => (
            <div key={i.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {i.crop_name} → {i.farmer_name}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {i.notes && <span className="italic mr-2">"{i.notes}"</span>}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge status={i.status} />
                  {i.status === "PENDING" && (
                    <button onClick={() => cancel(i.id)} className="text-xs text-red-500 hover:underline">Cancel</button>
                  )}
                </div>
              </div>
              {i.status === "ACCEPTED" && (
                <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700">
                  <CheckCircle size={12} className="inline mr-1" />
                  Accepted — contact information is now available.
                  {i.farmer_phone && <> Phone: <strong>{i.farmer_phone}</strong></>}
                  {i.farmer_email && <> · Email: <strong>{i.farmer_email}</strong></>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Farmer: Buyer Requirements ─────────────────────────────────────────────────
function FarmerBuyerRequirements() {
  const [requirements, setRequirements] = useState([]);
  const [sending, setSending] = useState({});
  const [msg, setMsg] = useState({});

  useEffect(() => {
    api.get("/api/farmer/buyer-requirements").then(r => setRequirements(r.data)).catch(() => {});
  }, []);

  async function sendInterest(req) {
    setSending(s => ({ ...s, [req.id]: true }));
    try {
      await api.post("/api/interests", {
        buyer_id: req.buyer_id,
        requirement_id: req.id,
        notes: `I have ${req.crop_name} available that may match your requirement.`,
      });
      setMsg(m => ({ ...m, [req.id]: "Request sent!" }));
    } catch (e) {
      const detail = e.response?.data?.detail;
      setMsg(m => ({ ...m, [req.id]: typeof detail === "string" ? detail : "Already sent or error." }));
    } finally { setSending(s => ({ ...s, [req.id]: false })); }
  }

  return (
    <div>
      <SectionTitle>Buyer Requirements</SectionTitle>
      <p className="text-xs text-gray-400 mb-3">Buyers looking for crops you grow</p>
      {requirements.length === 0 ? <EmptyState message="No matching buyer requirements found." /> : (
        <div className="space-y-2">
          {requirements.map(r => (
            <div key={r.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-800">{r.crop_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Required: {fmtQty(r.quantity)}
                    {r.minimum_price && <> · Min price: {fmt(r.minimum_price)}/kg</>}
                    {r.maximum_price && <> · Max: {fmt(r.maximum_price)}/kg</>}
                    {r.location && <> · 📍 {r.location}</>}
                  </p>
                  {r.description && <p className="text-xs text-gray-400 italic mt-0.5">{r.description}</p>}
                </div>
                <button
                  onClick={() => sendInterest(r)}
                  disabled={sending[r.id]}
                  className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 whitespace-nowrap"
                >
                  {sending[r.id] ? "Sending…" : "Send Interest"}
                </button>
              </div>
              {msg[r.id] && (
                <p className={`mt-1.5 text-xs ${msg[r.id].includes("sent") ? "text-green-600" : "text-amber-600"}`}>
                  {msg[r.id]}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Farmer: Received Requests ──────────────────────────────────────────────────
function ReceivedRequests() {
  const [interests, setInterests] = useState([]);

  const load = useCallback(async () => {
    try { const r = await api.get("/api/interests/received"); setInterests(r.data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function respond(id, action) {
    try { await api[action === "accept" ? "put" : "put"](`/api/interests/${id}/${action}`); load(); }
    catch {}
  }

  return (
    <div>
      <SectionTitle>Received Requests</SectionTitle>
      {interests.length === 0 ? <EmptyState message="No interest requests received yet." /> : (
        <div className="space-y-2">
          {interests.map(i => (
            <div key={i.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {i.buyer_name || "Buyer"} — {i.crop_name}
                  </p>
                  {i.notes && <p className="text-xs text-gray-500 italic mt-0.5">"{i.notes}"</p>}
                </div>
                <Badge status={i.status} />
              </div>
              {i.status === "PENDING" && (
                <div className="flex gap-2 mt-2">
                  <button onClick={() => respond(i.id, "accept")}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700">
                    <CheckCircle size={12} /> Accept
                  </button>
                  <button onClick={() => respond(i.id, "reject")}
                    className="flex items-center gap-1 px-3 py-1.5 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200">
                    <XCircle size={12} /> Reject
                  </button>
                </div>
              )}
              {i.status === "ACCEPTED" && (
                <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700">
                  <CheckCircle size={12} className="inline mr-1" />
                  Accepted — contact information shared.
                  {i.buyer_phone && <> Buyer phone: <strong>{i.buyer_phone}</strong></>}
                  {i.buyer_email && <> · Email: <strong>{i.buyer_email}</strong></>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function BuyersPage() {
  const { user } = useAuth();
  const role = user?.role?.toUpperCase();

  const [profile, setProfile] = useState(null);
  const [crops, setCrops] = useState([]);
  const [activeTab, setActiveTab] = useState(role === "BUYER" ? "requirements" : "buyer-reqs");

  const loadProfile = useCallback(async () => {
    if (role !== "BUYER") return;
    try { const r = await api.get("/api/buyer/profile"); setProfile(r.data); } catch {}
  }, [role]);

  useEffect(() => {
    loadProfile();
    api.get("/api/market/crops").then(r => setCrops(r.data)).catch(() => {
      // fallback: fetch all crops if market endpoint fails
      api.get("/api/farmer/crops").then(r => setCrops(r.data)).catch(() => {});
    });
  }, [loadProfile]);

  const buyerTabs = [
    { id: "requirements", label: "My Requirements", icon: ShoppingCart },
    { id: "find",         label: "Find Farmers",    icon: Search },
    { id: "sent",         label: "Requests",        icon: MessageSquare },
  ];

  const farmerTabs = [
    { id: "buyer-reqs",   label: "Buyer Requirements", icon: ShoppingCart },
    { id: "received",     label: "Received Requests",  icon: MessageSquare },
  ];

  const tabs = role === "BUYER" ? buyerTabs : farmerTabs;

  return (
    <div className="p-6 sm:p-8 max-w-3xl mx-auto">
      <PageHeader
        icon={Users}
        title={role === "BUYER" ? "Buyer Marketplace" : "Buyer-Farmer Connect"}
        subtitle={role === "BUYER"
          ? "Post requirements, find farmers, send interest requests"
          : "Browse buyer requirements and respond to interest requests"}
      />

      {/* Buyer profile card */}
      {role === "BUYER" && <BuyerProfileCard profile={profile} onRefresh={loadProfile} />}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5 gap-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === id
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {role === "BUYER" && (
        <>
          {activeTab === "requirements" && <MyRequirements crops={crops} />}
          {activeTab === "find"         && <FindFarmers />}
          {activeTab === "sent"         && <SentRequests />}
        </>
      )}
      {role === "FARMER" && (
        <>
          {activeTab === "buyer-reqs" && <FarmerBuyerRequirements />}
          {activeTab === "received"   && <ReceivedRequests />}
        </>
      )}
      {!["BUYER", "FARMER"].includes(role) && (
        <p className="text-sm text-gray-400">Log in as a buyer or farmer to use this feature.</p>
      )}
    </div>
  );
}
