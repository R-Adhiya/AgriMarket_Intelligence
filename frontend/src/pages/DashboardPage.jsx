import { TrendingUp, MapPin, IndianRupee, BarChart3, Info } from 'lucide-react'

const cards = [
  { label: 'Current Market Price', value: '₹0',  icon: TrendingUp,    hint: 'per quintal' },
  { label: 'Predicted Price',      value: '--',   icon: BarChart3,     hint: 'ML model — Phase 4' },
  { label: 'Best Market',          value: '--',   icon: MapPin,        hint: 'Market analysis — Phase 2' },
  { label: 'Expected Net Return',  value: '₹0',  icon: IndianRupee,   hint: 'After transport costs' },
]

export default function DashboardPage() {
  return (
    <div className="p-6 sm:p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Your agricultural market overview.</p>
      </div>

      {/* Phase notice */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4 mb-8 text-sm text-blue-800">
        <Info className="w-4 h-4 shrink-0 mt-0.5" />
        <span>
          <strong>Phase 1 — Architecture setup.</strong> Real market data, predictions, and
          recommendations will be available in later phases. Values below are placeholders only.
        </span>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ label, value, icon: Icon, hint }) => (
          <div key={label} className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
              <span className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-lg">
                <Icon className="w-4 h-4 text-gray-500" />
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-400 mt-1">{hint}</p>
          </div>
        ))}
      </div>

      {/* Placeholder sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-1">Price Trend</h2>
          <p className="text-sm text-gray-400">Chart will appear in Phase 2+</p>
          <div className="mt-4 h-32 bg-gray-50 rounded-lg border border-dashed border-gray-200 flex items-center justify-center text-xs text-gray-400">
            Market price chart — coming soon
          </div>
        </div>
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-1">Nearby Markets</h2>
          <p className="text-sm text-gray-400">Market list will appear in Phase 2+</p>
          <div className="mt-4 h-32 bg-gray-50 rounded-lg border border-dashed border-gray-200 flex items-center justify-center text-xs text-gray-400">
            Market comparison — coming soon
          </div>
        </div>
      </div>
    </div>
  )
}
