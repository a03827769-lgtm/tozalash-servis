"use client";

import { motion } from "framer-motion";
import { 
  TrendingUp, 
  Users, 
  Wallet, 
  Calendar,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";

const revenueData = [
  { name: "Dush", current: 4000, prev: 2400 },
  { name: "Sesh", current: 3000, prev: 1398 },
  { name: "Chor", current: 2000, prev: 9800 },
  { name: "Pay", current: 2780, prev: 3908 },
  { name: "Juma", current: 1890, prev: 4800 },
  { name: "Shan", current: 2390, prev: 3800 },
  { name: "Yak", current: 3490, prev: 4300 },
];

const activityData = [
  { name: "08:00", active: 12 },
  { name: "10:00", active: 25 },
  { name: "12:00", active: 40 },
  { name: "14:00", active: 38 },
  { name: "16:00", active: 55 },
  { name: "18:00", active: 45 },
  { name: "20:00", active: 20 },
];

const StatCard = ({ title, value, change, isPositive, icon: Icon, delay }: any) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.5 }}
    className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
  >
    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
      <Icon className="w-16 h-16" />
    </div>
    <div className="flex justify-between items-start mb-4">
      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
        <Icon className="w-5 h-5 text-blue-400" />
      </div>
      <div className={`flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-full ${isPositive ? 'text-emerald-400 bg-emerald-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
        {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        {change}%
      </div>
    </div>
    <h3 className="text-slate-400 text-sm font-medium mb-1">{title}</h3>
    <p className="text-2xl font-bold text-slate-100">{value}</p>
  </motion.div>
);

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Xush kelibsiz, Admin!</h1>
          <p className="text-slate-400 text-sm mt-1">Tizimning bugungi holati va ko'rsatkichlari</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 glass-panel rounded-xl text-sm font-medium hover:bg-slate-800/50 transition-colors">
            Hisobot yuklash
          </button>
          <button className="btn-primary px-4 py-2 rounded-xl text-sm font-medium">
            Yangi buyurtma
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Umumiy Daromad" value="12,450,000 UZS" change="12.5" isPositive={true} icon={Wallet} delay={0.1} />
        <StatCard title="Faol Buyurtmalar" value="45" change="8.2" isPositive={true} icon={Calendar} delay={0.2} />
        <StatCard title="Yangi Mijozlar" value="128" change="3.1" isPositive={false} icon={Users} delay={0.3} />
        <StatCard title="Xizmat Samaradorligi" value="94%" change="5.4" isPositive={true} icon={TrendingUp} delay={0.4} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="lg:col-span-2 glass-panel p-6 rounded-2xl"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-slate-100">Daromadlar dinamikasi (AI Bashorati bilan)</h3>
            <select className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-1 text-sm outline-none focus:border-blue-500/50">
              <option>Shu hafta</option>
              <option>O'tgan hafta</option>
              <option>Shu oy</option>
            </select>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCurrent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPrev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value/1000}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px', color: '#f8fafc' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Area type="monotone" dataKey="current" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCurrent)" name="Haqiqiy" />
                <Area type="monotone" dataKey="prev" stroke="#8b5cf6" strokeWidth={3} strokeDasharray="5 5" fillOpacity={1} fill="url(#colorPrev)" name="AI Bashorati" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="glass-panel p-6 rounded-2xl flex flex-col"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-slate-100">Tizim Yuklamasi</h3>
          </div>
          <div className="flex-1 h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: '#1e293b' }}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                />
                <Bar dataKey="active" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Faol tozalashlar" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700/50 flex justify-between items-center text-sm">
            <span className="text-slate-400">Holat: <span className="text-emerald-400">Normal</span></span>
            <span className="text-blue-400 cursor-pointer hover:text-blue-300">Batafsil &rarr;</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
