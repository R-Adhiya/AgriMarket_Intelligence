import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import {
  TrendingUp, BarChart3, RefreshCw, AlertCircle, ChevronDown, Info, Truck,
} from "lucide-react";
import { getCropsWithPrices, comparePrices, getPriceHistory } from "../services/marketService";
import { getAllMarketTransport } from "../services/transportService";

const PERIOD_OPTIONS = [
  { label: "7 days",  value: 7  },
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
];

export default function MarketsPage() {
  const [crops, setCrops]               = useState([]);
  const [selectedCrop, setSelectedCrop] = useState(null);
  const [comparison, setComparison]     = useState(null);
  const [history, setHistory]           = useState(null);
  const [transport, setTransport]       = useState(null);   // { markets: [...] }
  const [period, setPeriod]             = useState(30);
  const [quantity, setQuantity]         = useState(10);
  const [loading, setLoading]           = useState(false);
  const [histLoading, setHistLoading]   = useState(false);
  const [transportLoading, setTL]       = useState(false);
  const [error, setError]               = useState("");
  const [transportError, setTE]         = useState("");

  // Load crops on mount
  useEffect(() => {
    getCropsWithPrices()
      .then((data) => {
        setCrops(data);
        if (data.length > 0) setSelectedCrop(data[0]);
      })
      .catch(() => setError("Could not load crop list. Is the backend running?"));
  }, []);

  // Load price comparison when crop changes
  useEffect(() => {
    if (!selectedCrop) return;
    setLoading(true);
    setError("");
    comparePrices(selectedCrop.id)
      .then(setComparison)
      .catch(() => setError("Could not load price data."))
      .finally(() => setLoading(false));
  }, [selectedCrop]);

  // Load historical prices
  useEffect(() => {
    if (!selectedCrop) return;
    setHistLoading(true);
    getPriceHistory(selectedCrop.id, { days: period })
      .then(setHistory)
      .catch(() => {})
      .finally(() => setHistLoading(false));
  }, [selectedCrop, period]);

  // Load transport estimates
  useEffect(() => {
    setTL(true);
    setTE("");
    getAllMarketTransport(quantity)
      .then(setTransport)
      .catch((err) => {
        if (err.response?.status === 422) {
          setTE("Add your district to your profile to see transport estimates.");
        } else {
          setTE("Transport estimates unavailable.");
        }
      })
      .finally(() => setTL(false));
  }, [quantity]);

  // Build a market_id → transport lookup for the table
  const transportByMarket = {};
  if (transport?.markets) {
    for (const m of transport.markets) {
      transportByMarket[m.market_id] = m;
    }
  }

  // Build chart data
  const chartData = (() => {
    if (!history?.history?.length) return [];
    const byDate = {};
    for (const h of history.history) {
      if (!byDate[h.price_date]) byDate[h.price_date] = { date: h.price_date };
      byDate[h.price_date][h.market_name] = h.modal_price;
    }
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  })();

  const marketNames = history?.history
    ? [...new Set(history.history.map((h) => h.market_name))]
    : [];

  const COLORS = ["#16a34a", "#2563eb", "#d97706", "#dc2626", "#7c3aed"];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <TrendingUp size={22} className="text-green-700" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Intelligence</h1>
          <p className="text-sm text-gray-500">Compare crop prices and transport costs across markets</p>
        </div>
      </div>

      {/* Data notice */}
      <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
        <Info size={13} className="mt-0.5 shrink-0" />
        Development sample data — not real-time government prices or commercial transport quotes.
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {/* Controls row */}
      <div className="flex flex-wrap gap-4 items-end">
        {/* Crop selector */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Crop</label>
          {crops.length === 0 ? (
            <p className="text-sm text-gray-400">No crops with price data available.</p>
          ) : (
            <div className="relative">
              <select
                value={selectedCrop?.id ?? ""}
                onChange={(e) => {
                  const c = crops.find((cr) => cr.id === parseInt(e.target.value));
                  setSelectedCrop(c || null);
                }}
                className="appearance-none border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm
                           focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
              >
                {crops.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.unit})</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          )}
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Quantity (quintals)</label>
          <input
            type="number"
            min="1"
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      </div>

      {/* Current price comparison table */}
      {selectedCrop && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800 flex items-center gap-2">
              <BarChart3 size={16} className="text-green-700" />
              Current Market Prices — {selectedCrop.name}
            </h2>
            {(loading || transportLoading) && <RefreshCw size={14} className="animate-spin text-gray-400" />}
          </div>

          {transportError && (
            <div className="text-xs text-amber-700 bg-amber-50 rounded px-3 py-1.5 mb-3 flex items-center gap-1">
              <Truck size={12} /> {transportError}
            </div>
          )}

          {!loading && comparison?.prices?.length === 0 && (
            <p className="text-sm text-gray-400">No current price data available for this crop.</p>
          )}

          {!loading && comparison?.prices?.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 font-medium">Market</th>
                    <th className="pb-2 font-medium">Location</th>
                    <th className="pb-2 font-medium text-right">Modal ₹</th>
                    <th className="pb-2 font-medium text-right">Min–Max ₹</th>
                    <th className="pb-2 font-medium text-right">Distance</th>
                    <th className="pb-2 font-medium text-right">Est. Transport</th>
                    <th className="pb-2 font-medium text-right">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.prices.map((p, i) => {
                    const t = transportByMarket[p.market_id];
                    return (
                      <tr key={i} className="border-b border-gray-50 last:border-0">
                        <td className="py-2.5 font-medium text-gray-800">{p.market_name}</td>
                        <td className="py-2.5 text-gray-500">
                          {[p.district, p.state].filter(Boolean).join(", ")}
                        </td>
                        <td className="py-2.5 text-right font-semibold text-green-700">₹{p.modal_price}</td>
                        <td className="py-2.5 text-right text-gray-400 text-xs">₹{p.min_price}–{p.max_price}</td>
                        <td className="py-2.5 text-right text-gray-500 text-xs">
                          {t ? `${t.distance_km} km` : "—"}
                        </td>
                        <td className="py-2.5 text-right text-gray-600 text-xs">
                          {t ? `₹${t.estimated_transport_cost}` : "—"}
                        </td>
                        <td className="py-2.5 text-right text-gray-400 text-xs">{p.price_date}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p className="text-xs text-gray-300 mt-2">
                Sorted by modal price (highest first). Transport: estimated only, not a commercial quote.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Historical price chart */}
      {selectedCrop && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h2 className="font-semibold text-gray-800 flex items-center gap-2">
              <TrendingUp size={16} className="text-green-700" />
              Historical Price Trend — {selectedCrop.name}
            </h2>
            <div className="flex gap-1">
              {PERIOD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPeriod(opt.value)}
                  className={`px-3 py-1 text-xs rounded-lg border transition ${
                    period === opt.value
                      ? "bg-green-700 text-white border-green-700"
                      : "border-gray-300 text-gray-500 hover:border-gray-400"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {histLoading && (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
              <RefreshCw size={16} className="animate-spin mr-2" /> Loading…
            </div>
          )}
          {!histLoading && chartData.length === 0 && (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
              No historical data available for this period.
            </div>
          )}
          {!histLoading && chartData.length > 0 && (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} tickFormatter={(v) => `₹${v}`} width={55} />
                <Tooltip formatter={(value, name) => [`₹${value}`, name]} labelFormatter={(l) => `Date: ${l}`} contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {marketNames.map((name, idx) => (
                  <Line key={name} type="monotone" dataKey={name}
                    stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* Transport summary card */}
      {transport?.markets?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-800 flex items-center gap-2 mb-3">
            <Truck size={16} className="text-green-700" />
            Transport Distance Summary
            <span className="text-xs font-normal text-gray-400 ml-1">(sorted by distance)</span>
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                  <th className="pb-2 font-medium">Market</th>
                  <th className="pb-2 font-medium">Location</th>
                  <th className="pb-2 font-medium text-right">Distance</th>
                  <th className="pb-2 font-medium text-right">Est. Cost ({quantity} qtl)</th>
                </tr>
              </thead>
              <tbody>
                {transport.markets.map((m) => (
                  <tr key={m.market_id} className="border-b border-gray-50 last:border-0">
                    <td className="py-2.5 font-medium text-gray-800">{m.market_name}</td>
                    <td className="py-2.5 text-gray-500">{[m.district, m.state].filter(Boolean).join(", ")}</td>
                    <td className="py-2.5 text-right text-gray-600">{m.distance_km} km</td>
                    <td className="py-2.5 text-right font-medium text-gray-800">₹{m.estimated_transport_cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-gray-300 mt-2">
              Estimated only — not a commercial quote. From: {transport.farmer_district || "your location"}.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
