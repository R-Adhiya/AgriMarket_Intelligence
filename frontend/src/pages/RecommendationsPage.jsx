import { useEffect, useState } from "react";
import {
  Lightbulb, ChevronDown, RefreshCw, AlertCircle, Info,
  TrendingUp, Truck, DollarSign, MapPin, CheckCircle,
} from "lucide-react";
import { getCropsWithPrices } from "../services/marketService";
import { getRecommendation, getRecommendationHistory } from "../services/recommendationService";

const BASIS_OPTIONS = [
  { value: "current",   label: "Current price" },
  { value: "predicted", label: "Predicted price (ML)" },
];

export default function RecommendationsPage() {
  const [crops, setCrops]         = useState([]);
  const [crop, setCrop]           = useState(null);
  const [quantityKg, setQty]      = useState(500);
  const [priceBasis, setBasis]    = useState("current");
  const [result, setResult]       = useState(null);
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");

  useEffect(() => {
    getCropsWithPrices()
      .then((data) => { setCrops(data); if (data.length > 0) setCrop(data[0]); })
      .catch(() => setError("Could not load crop list."));
    getRecommendationHistory().then(setHistory).catch(() => {});
  }, []);

  async function handleRecommend() {
    if (!crop || quantityKg <= 0) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await getRecommendation({ cropId: crop.id, quantityKg, priceBasis });
      setResult(data);
      getRecommendationHistory().then(setHistory).catch(() => {});
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(msg || "Could not generate recommendation. Check your farmer profile has a district set.");
    } finally {
      setLoading(false);
    }
  }

  const rec = result?.recommended_market;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Lightbulb size={22} className="text-green-700" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Recommendation</h1>
          <p className="text-sm text-gray-500">Where should I sell to get the best net return?</p>
        </div>
      </div>

      <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
        <Info size={13} className="mt-0.5 shrink-0" />
        Recommended based on available price and transport estimates only — not a guaranteed market price or commercial quote.
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Crop */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Crop</label>
            <div className="relative">
              <select value={crop?.id ?? ""} onChange={(e) => setCrop(crops.find(c => c.id === parseInt(e.target.value)))}
                className="appearance-none border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white min-w-[160px]">
                {crops.map(c => <option key={c.id} value={c.id}>{c.name} ({c.unit})</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Quantity (kg)</label>
            <input type="number" min="1" value={quantityKg}
              onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
          </div>

          {/* Price basis */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Price basis</label>
            <div className="relative">
              <select value={priceBasis} onChange={(e) => setBasis(e.target.value)}
                className="appearance-none border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white">
                {BASIS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          </div>

          <button onClick={handleRecommend} disabled={loading || !crop}
            className="flex items-center gap-2 bg-green-700 hover:bg-green-800 disabled:bg-green-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition">
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Lightbulb size={14} />}
            {loading ? "Analysing…" : "Get Recommendation"}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
          <AlertCircle size={15} className="mt-0.5 shrink-0" /> {error}
        </div>
      )}

      {/* Recommendation result */}
      {result && (
        <>
          {/* Recommended market hero */}
          {rec ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle size={18} className="text-green-600" />
                <span className="text-sm font-semibold text-green-700 uppercase tracking-wide">Recommended Market</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">{rec.market_name}</h2>
              <p className="text-sm text-gray-500 mb-4">
                {[rec.district, rec.state].filter(Boolean).join(", ")} · {priceBasis === "predicted" ? "Estimated" : "Current"} price: ₹{rec.price_per_unit}/{rec.price_unit}
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <Metric icon={<TrendingUp size={14} />} label="Gross Revenue"   value={`₹${rec.gross_revenue.toLocaleString()}`} />
                <Metric icon={<Truck size={14} />}      label="Est. Transport"  value={`₹${rec.transport_cost.toLocaleString()}`} />
                <Metric icon={<DollarSign size={14} />} label="Net Revenue"     value={`₹${rec.net_revenue.toLocaleString()}`} highlight />
                <Metric icon={<MapPin size={14} />}     label="Distance"        value={`${rec.distance_km} km`} />
              </div>
              <div className="bg-white rounded-lg border border-green-100 px-4 py-3 text-sm text-gray-700">
                <span className="font-medium text-green-700">Why this market? </span>
                {result.explanation}
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-sm text-yellow-800">
              No eligible markets found. {result.explanation}
            </div>
          )}

          {/* Comparison table */}
          {result.comparison.length > 1 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-800 mb-3 text-sm">Market Comparison</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 font-medium">Market</th>
                      <th className="pb-2 font-medium text-right">Price/unit</th>
                      <th className="pb-2 font-medium text-right">Distance</th>
                      <th className="pb-2 font-medium text-right">Transport</th>
                      <th className="pb-2 font-medium text-right">Gross</th>
                      <th className="pb-2 font-medium text-right">Net ▼</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.comparison.map((m) => (
                      <tr key={m.market_id}
                        className={`border-b border-gray-50 last:border-0 ${m.is_recommended ? "bg-green-50" : ""}`}>
                        <td className="py-2.5 font-medium text-gray-800">
                          {m.is_recommended && <span className="text-green-600 mr-1">★</span>}
                          {m.market_name}
                        </td>
                        <td className="py-2.5 text-right text-gray-600">₹{m.price_per_unit}</td>
                        <td className="py-2.5 text-right text-gray-500">{m.distance_km} km</td>
                        <td className="py-2.5 text-right text-gray-500">₹{m.transport_cost.toLocaleString()}</td>
                        <td className="py-2.5 text-right text-gray-600">₹{m.gross_revenue.toLocaleString()}</td>
                        <td className={`py-2.5 text-right font-semibold ${m.is_recommended ? "text-green-700" : "text-gray-800"}`}>
                          ₹{m.net_revenue.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-300 mt-2">
                ★ Recommended. Sorted by net revenue (highest first). {result.currency} · {result.recommendation_method}
              </p>
            </div>
          )}

          {/* Excluded markets */}
          {result.excluded_markets.length > 0 && (
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Excluded markets</p>
              <ul className="text-xs text-gray-400 space-y-0.5">
                {result.excluded_markets.map((e, i) => (
                  <li key={i}>{e.market_name} — {e.reason}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-800 mb-3 text-sm">Recent Recommendations</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Crop</th>
                  <th className="pb-2 font-medium">Market</th>
                  <th className="pb-2 font-medium text-right">Net Rev</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 5).map((h) => (
                  <tr key={h.id} className="border-b border-gray-50 last:border-0">
                    <td className="py-2 text-gray-500 text-xs">{h.created_at.slice(0, 10)}</td>
                    <td className="py-2 text-gray-700">{h.crop_name}</td>
                    <td className="py-2 text-gray-700">{h.market_name}</td>
                    <td className="py-2 text-right font-medium text-green-700">
                      {h.expected_net_revenue ? `₹${h.expected_net_revenue.toLocaleString()}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ icon, label, value, highlight }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-green-200 bg-white" : "border-gray-100 bg-white"}`}>
      <div className={`flex items-center gap-1 text-xs mb-1 ${highlight ? "text-green-600" : "text-gray-400"}`}>
        {icon} {label}
      </div>
      <p className={`text-base font-bold ${highlight ? "text-green-700" : "text-gray-800"}`}>{value}</p>
    </div>
  );
}
