import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Users, ShoppingBag, CreditCard, Sparkles, BrainCircuit } from 'lucide-react';
import LiveMap from '../components/LiveMap';

const revData = [
  { name: 'Mon', revenue: 4000 },
  { name: 'Tue', revenue: 3000 },
  { name: 'Wed', revenue: 2000 },
  { name: 'Thu', revenue: 2780 },
  { name: 'Fri', revenue: 1890 },
  { name: 'Sat', revenue: 2390 },
  { name: 'Sun', revenue: 3490 },
];

const serviceData = [
  { name: 'Deep Clean', value: 400 },
  { name: 'Standard', value: 300 },
  { name: 'Move in/out', value: 300 },
  { name: 'Post-construction', value: 200 },
];
const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#ec4899'];

const statCards = [
  { title: "Total Revenue", value: "8,450,000 UZS", icon: CreditCard, trend: "+12%" },
  { title: "Active Workers", value: "18", icon: Users, trend: "+4%" },
  { title: "AI Accuracy", value: "98.2%", icon: BrainCircuit, trend: "+1.2%" },
  { title: "Auto-Assigned Orders", value: "85%", icon: Sparkles, trend: "+5%" }
];

const liveOrders = [
  { id: 'ORD-001', client: 'Aziz R.', service: 'Deep Clean', status: 'In Progress', aiConfidence: '99%', amount: '450,000 UZS' },
  { id: 'ORD-002', client: 'Malika T.', service: 'Standard', status: 'Pending', aiConfidence: '95%', amount: '200,000 UZS' },
  { id: 'ORD-003', client: 'Timur K.', service: 'Move in', status: 'Completed', aiConfidence: '100%', amount: '800,000 UZS' },
];

const Dashboard = () => {
  return (
    <div className="pb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">AI Operations Control</h1>
          <p className="text-slate-400 font-light">Real-time telemetry and automation metrics</p>
        </div>
        <button className="px-6 py-2.5 rounded-full bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 font-medium transition-all hover:scale-105 active:scale-95 flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          Generate Insight Report
        </button>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, idx) => (
          <div key={idx} className="group relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:border-indigo-500/30 overflow-hidden">
            <div className="absolute top-0 right-0 p-32 bg-indigo-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-indigo-500/10 transition-colors" />
            <div className="relative flex justify-between items-start mb-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 ring-1 ring-inset ring-indigo-500/20 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300">
                <stat.icon size={22} strokeWidth={2} />
              </div>
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide ${stat.trend.startsWith('+') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'}`}>{stat.trend}</span>
            </div>
            <div className="relative">
              <h3 className="text-slate-400 text-sm font-medium mb-1">{stat.title}</h3>
              <div className="text-2xl font-bold text-slate-100 tracking-tight">{stat.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 transition-all hover:border-white/20">
          <h3 className="text-lg font-semibold text-slate-200 mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            Revenue Forecast & Actuals
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} axisLine={false} tickLine={false} dy={10} />
                <YAxis stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} axisLine={false} tickLine={false} dx={-10} />
                <Tooltip 
                  contentStyle={{ background: 'rgba(9, 9, 11, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }} 
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorRev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 transition-all hover:border-white/20">
          <h3 className="text-lg font-semibold text-slate-200 mb-6">Service Intelligence</h3>
          <div className="h-[240px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={serviceData} cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={5} dataKey="value" stroke="none">
                  {serviceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} className="hover:opacity-80 transition-opacity" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'rgba(9, 9, 11, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} itemStyle={{ color: '#f8fafc' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <span className="block text-2xl font-bold text-slate-100">1.2k</span>
                <span className="block text-xs text-slate-400">Total Tasks</span>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-3 justify-center mt-6">
            {serviceData.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[idx] }}></div>
                <span className="text-slate-300">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live Orders Table */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 mb-8 overflow-hidden transition-all hover:border-white/20">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-purple-400" />
            AI Dispatched Active Tasks
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Task ID</th>
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Client</th>
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Service Type</th>
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Auto-Assign Confidence</th>
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Amount</th>
                <th className="py-4 px-4 text-slate-400 font-medium text-sm">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {liveOrders.map((order, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-colors group">
                  <td className="py-4 px-4 text-slate-200 font-medium font-mono text-sm">{order.id}</td>
                  <td className="py-4 px-4 text-slate-300">{order.client}</td>
                  <td className="py-4 px-4 text-slate-300">{order.service}</td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-white/10 rounded-full h-1.5 max-w-[80px]">
                        <div className="bg-gradient-to-r from-purple-400 to-indigo-500 h-1.5 rounded-full" style={{ width: order.aiConfidence }}></div>
                      </div>
                      <span className="text-xs text-slate-400 font-mono">{order.aiConfidence}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-slate-200 font-medium text-sm">{order.amount}</td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                      order.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                      order.status === 'In Progress' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 
                      'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}>
                      {order.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3D Map Real-Time Tracking */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 transition-all hover:border-white/20">
        <h3 className="text-lg font-semibold text-slate-200 mb-6 flex items-center gap-2">
          Global Operations Map
        </h3>
        <div className="rounded-xl overflow-hidden border border-white/10">
          <LiveMap />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
