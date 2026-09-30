import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Brain, ChevronDown, RefreshCw, AlertCircle, Info } from "lucide-react";
import { getCropsWithPrices, comparePrices } from "../services/marketService";
import { getPricePrediction } from "../services/predictionService";

const HORIZONS = [
  { label: "Next day",  value: 1 },
  { label: "3 days",   value: 3 },
  { label: "7 days",   value: 7 },
];

export default function PredictionPage() {
  const [crops, setCrops]         = useState([]);
  const [markets, setMarkets]     = useState([]);
  const [crop, setCrop]           = useState(null);
  const [market, setMarket]       = useState(null);
  const [horizon, setHorizon]     = useState(1);
  const [result, setResult]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");

  // Load crops on mount
  useEffect(() => {
    getCropsWithPrices()
      .then((data) => {
        setCrops(data);
        if (data.length > 0) setCrop(data[0]);
      })
      .catch(() => setError("Could not load crop list."));
  }, []);

  // Load markets when crop changes
  useEffect(() => {
    if (!crop) return;
    comparePrices(crop.id)
      .then((data) => {
        const mktList = data.prices.map((p) => ({
          id: p.market_id, name: p.market_name, district: p.district,
        }));
        setMarkets(mktList);
        if (mktList.length > 0) setMarket(mktList[0]);
      })
      .catch(() => setMarkets([]));
  }, [crop]);

  async function handlePredict() {
    if (!crop || !market) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await getPricePrediction(crop.id, market.id, horizon);
      setResult(data);
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(msg || "Prediction unavailable. The model may not be trained for this combination.");
    } finally {
      setLoading(false);
    }
  }

  // Build chart data: historical (last known) + predictions
  const chartData = (() => {
    if (!result) return [];
    const points = [];
    // Anchor: last known price
    points.push({
      date:     result.latest_known_date,
      observed: result.latest_known_price,
      predicted: null,
    });
    // Predictions
    for (const p of result.predictions) {
      points.push({
        date:     p.date,
        observed: null,
        predicted: p.predicted_price,
      });
    }
    return points;
  })();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Brain size={22} className="text-green-700" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Price Prediction</h1>
          <p className="text-sm text-gray-500">ML-based estimated future crop prices</p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
        <Info size={13} className="mt-0.5 shrink-0" />
        Predictions are estimates based on available historical data and should not
        be treated as guaranteed market prices. Trained on synthetic development data only.
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Crop */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Crop</label>
            <Select
              value={crop?.id ?? ""}
              onChange={(v) => setCrop(crops.find((c) => c.id === parseInt(v)))}
              options={crops.map((c) => ({ value: c.id, label: `${c.name} (${c.unit})` }))}
            />
          </div>

          {/* Market */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Market</label>
            <Select
              value={market?.id ?? ""}
              onChange={(v) => setMarket(markets.find((m) => m.id === parseInt(v)))}
              options={markets.map((m) => ({ value: m.id, label: m.name }))}
            />
          </div>

          {/* Horizon */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Horizon</label>
            <div className="flex gap-1">
              {HORIZONS.map((h) => (
                <button
                  key={h.value}
                  onClick={() => setHorizon(h.value)}
                  className={`px-3 py-2 text-xs rounded-lg border transition ${
                    horizon === h.value
                      ? "bg-green-700 text-white border-green-700"
                      : "border-gray-300 text-gray-500 hover:border-gray-400"
                  }`}
                >
                  {h.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading || !crop || !market}
            className="flex items-center gap-2 bg-green-700 hover:bg-green-800
                       disabled:bg-green-400 text-white text-sm font-medium
                       px-4 py-2 rounded-lg transition"
          >
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Brain size={14} />}
            {loading ? "Predicting…" : "Predict"}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
          <AlertCircle size={15} className="mt-0.5 shrink-0" /> {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Current price"   value={`₹${result.latest_known_price}`} sub={result.latest_known_date} />
            <StatCard label="Predicted (day 1)" value={`₹${result.predictions[0]?.predicted_price ?? "—"}`} sub={result.predictions[0]?.date} highlight />
            {result.predictions.length >= 3 && (
              <StatCard label="Predicted (day 3)" value={`₹${result.predictions[2]?.predicted_price ?? "—"}`} sub={result.predictions[2]?.date} />
            )}
            <StatCard label="Model" value={result.model_used} sub={`${result.crop} · ${result.market_name}`} />
          </div>

          {/* Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-4 text-sm">
              Price Trend — {result.crop} @ {result.market_name}
            </h2>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }} />
                <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} tickFormatter={(v) => `₹${v}`} width={55} />
                <Tooltip
                  formatter={(value, name) => value !== null ? [`₹${value}`, name] : [null, name]}
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine
                  x={result.latest_known_date}
                  stroke="#d97706"
                  strokeDasharray="4 2"
                  label={{ value: "Today", fontSize: 10, fill: "#d97706" }}
                />
                <Line type="monotone" dataKey="observed"  name="Observed"  stroke="#16a34a" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                <Line type="monotone" dataKey="predicted" name="Estimated" stroke="#2563eb" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 4 }} connectNulls />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-300 mt-2">
              Dashed blue = estimated price. {result.disclaimer}
            </p>
          </div>

          {/* Prediction table */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3 text-sm">Estimated Prices</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium text-right">Estimated Price</th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((p) => (
                  <tr key={p.date} className="border-b border-gray-50 last:border-0">
                    <td className="py-2 text-gray-700">{p.date}</td>
                    <td className="py-2 text-right font-medium text-green-700">₹{p.predicted_price}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// ── Small components ──────────────────────────────────────────────────────────

function Select({ value, onChange, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm
                   focus:outline-none focus:ring-2 focus:ring-green-500 bg-white min-w-[160px]"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
    </div>
  );
}

function StatCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "border-green-200 bg-green-50" : "border-gray-200 bg-white"}`}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-xl font-bold truncate ${highlight ? "text-green-700" : "text-gray-800"}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5 truncate">{sub}</p>}
    </div>
  );
}
