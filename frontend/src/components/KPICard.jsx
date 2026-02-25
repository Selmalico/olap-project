import { DollarSign, TrendingUp, Percent, ShoppingCart, Package, Globe } from 'lucide-react'

const ICONS = {
  dollar: DollarSign,
  'trending-up': TrendingUp,
  percent: Percent,
  'shopping-cart': ShoppingCart,
  package: Package,
  globe: Globe,
}

const COLORS = {
  blue: 'from-blue-600/20 to-blue-600/5 border-blue-500/20 text-blue-400',
  green: 'from-emerald-600/20 to-emerald-600/5 border-emerald-500/20 text-emerald-400',
  purple: 'from-purple-600/20 to-purple-600/5 border-purple-500/20 text-purple-400',
  orange: 'from-orange-600/20 to-orange-600/5 border-orange-500/20 text-orange-400',
  teal: 'from-teal-600/20 to-teal-600/5 border-teal-500/20 text-teal-400',
  pink: 'from-pink-600/20 to-pink-600/5 border-pink-500/20 text-pink-400',
}

export default function KPICard({ label, value, icon, color = 'blue' }) {
  const Icon = ICONS[icon] || DollarSign
  const colorClass = COLORS[color] || COLORS.blue

  return (
    <div className={`shrink-0 flex items-center gap-3 px-4 py-2.5 rounded-xl border bg-gradient-to-br ${colorClass} min-w-[160px]`}>
      <Icon size={18} className="shrink-0" />
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-400 leading-none">{label}</p>
        <p className="text-sm font-bold text-white mt-0.5 leading-none">{value}</p>
      </div>
    </div>
  )
}
