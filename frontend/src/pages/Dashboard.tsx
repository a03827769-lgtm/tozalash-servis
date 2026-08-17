import React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts'
import { useAppStore } from '@/store/useAppStore'
import { Users, TrendingUp, CheckCircle, Clock, Award, Gift, Megaphone } from 'lucide-react'

const monthlyRevenue = [
  { name: 'Yanvar', daromad: 4000, xarajat: 2400 },
  { name: 'Fevral', daromad: 3000, xarajat: 1398 },
  { name: 'Mart', daromad: 5000, xarajat: 4800 },
  { name: 'Aprel', daromad: 4500, xarajat: 3908 },
  { name: 'May', daromad: 6000, xarajat: 4800 },
  { name: 'Iyun', daromad: 7000, xarajat: 3800 },
]

const workerPerformance = [
  { name: 'Sardor', orders: 40, rating: 4.8 },
  { name: 'Aziz', orders: 30, rating: 4.5 },
  { name: 'Alisher', orders: 55, rating: 4.9, isEmployeeOfMonth: true },
  { name: 'Dilshod', orders: 20, rating: 4.2 },
]

const marketingStats = [
  { title: "Berilgan Cashback", value: "2.5M UZS" },
  { title: "Yangi Mijozlar (Referral)", value: "142" },
  { title: "Faol Promokodlar", value: "5" },
]

export const Dashboard = () => {
  const theme = useAppStore((state) => state.theme)
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  
  const chartColors = {
    revenue: isDark ? '#3b82f6' : '#2563eb',
    expense: isDark ? '#ef4444' : '#dc2626',
    orders: isDark ? '#10b981' : '#059669',
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#4b5563',
    tooltipBg: isDark ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)',
  }

  return (
    <div className="p-6 md:p-8 space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
          Boshqaruv Paneli
        </h1>
        <p className="text-gray-500 dark:text-gray-400 font-medium">Asosiy ko'rsatkichlar va statistika</p>
      </div>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: "Umumiy Daromad", value: "45.2M UZS", icon: <TrendingUp size={24} />, color: "from-blue-500 to-indigo-500" },
          { title: "Faol Mijozlar", value: "1,245", icon: <Users size={24} />, color: "from-emerald-500 to-teal-500" },
          { title: "Bajarilgan Buyurtmalar", value: "892", icon: <CheckCircle size={24} />, color: "from-purple-500 to-pink-500" },
          { title: "Kutilyotgan Buyurtmalar", value: "34", icon: <Clock size={24} />, color: "from-amber-500 to-orange-500" }
        ].map((stat, i) => (
          <div key={i} className="group relative overflow-hidden rounded-2xl bg-white dark:bg-gray-800/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 dark:border-gray-700/50 backdrop-blur-xl">
            <div className={`absolute top-0 right-0 -mr-8 -mt-8 h-32 w-32 rounded-full bg-gradient-to-br ${stat.color} opacity-10 group-hover:opacity-20 transition-opacity blur-2xl`}></div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{stat.title}</p>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</h3>
              </div>
              <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color} text-white shadow-md`}>
                {stat.icon}
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-emerald-500 font-semibold flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                12.5%
              </span>
              <span className="text-gray-400 ml-2">o'tgan oydan</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Revenue Chart */}
        <div className="rounded-2xl bg-white dark:bg-gray-800/50 p-6 shadow-lg border border-gray-100 dark:border-gray-700/50 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Oylik Moliyaviy Holat</h2>
            <select className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2 dark:text-white outline-none">
              <option>2026 Yil</option>
              <option>2025 Yil</option>
            </select>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyRevenue} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorDaromad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColors.revenue} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={chartColors.revenue} stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorXarajat" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColors.expense} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={chartColors.expense} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="name" stroke={chartColors.text} axisLine={false} tickLine={false} dy={10} />
                <YAxis stroke={chartColors.text} axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: chartColors.tooltipBg, borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }} 
                  itemStyle={{ fontWeight: 600 }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Area type="monotone" dataKey="daromad" name="Daromad" stroke={chartColors.revenue} strokeWidth={3} fillOpacity={1} fill="url(#colorDaromad)" />
                <Area type="monotone" dataKey="xarajat" name="Xarajatlar" stroke={chartColors.expense} strokeWidth={3} fillOpacity={1} fill="url(#colorXarajat)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Worker Performance Chart */}
        <div className="rounded-2xl bg-white dark:bg-gray-800/50 p-6 shadow-lg border border-gray-100 dark:border-gray-700/50 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Ishchilar Reytingi</h2>
              <div className="flex items-center gap-2 mt-2">
                <Award className="text-amber-500" size={20} />
                <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">Oylik Xodim: Alisher (4.9 ⭐)</span>
              </div>
            </div>
            <button className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">Barchasini ko'rish</button>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={workerPerformance} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }} barSize={24}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={true} vertical={false} />
                <XAxis type="number" stroke={chartColors.text} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke={chartColors.text} axisLine={false} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: isDark ? '#374151' : '#f3f4f6' }} 
                  contentStyle={{ backgroundColor: chartColors.tooltipBg, borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }} 
                />
                <Bar dataKey="rating" name="Reyting" fill={chartColors.orders} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Marketing & Cashback */}
        <div className="rounded-2xl bg-white dark:bg-gray-800/50 p-6 shadow-lg border border-gray-100 dark:border-gray-700/50 backdrop-blur-xl col-span-1 lg:col-span-2">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-pink-100 dark:bg-pink-900/30 rounded-xl text-pink-600 dark:text-pink-400">
              <Megaphone size={24} />
            </div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Marketing & Cashback</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {marketingStats.map((stat, i) => (
              <div key={i} className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-600/50">
                <div className="text-gray-500 dark:text-gray-400 mb-2 font-medium">{stat.title}</div>
                <div className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                  <Gift className="text-indigo-500" size={20} />
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
