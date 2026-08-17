import React from 'react';

export default function Dashboard() {
  return (
    <div className="min-h-screen p-6 lg:p-12 font-[family-name:var(--font-geist-sans)]">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 animate-float" style={{ animationDuration: '8s' }}>
        <div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-2 glow-text">
            Tozalash Servis AI <span className="text-indigo-500">CRM</span>
          </h1>
          <p className="text-slate-400 text-lg">Omnichannel boshqaruv va AI analitikasi</p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-4">
          <div className="flex -space-x-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className={`w-10 h-10 rounded-full border-2 border-slate-900 bg-indigo-${300+i*100} flex items-center justify-center text-xs font-bold text-white z-${10-i}`}>
                W{i}
              </div>
            ))}
            <div className="w-10 h-10 rounded-full border-2 border-slate-900 glass flex items-center justify-center text-xs font-bold text-slate-300 z-0">
              +12
            </div>
          </div>
          <button className="px-6 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-all shadow-[0_0_15px_rgba(79,70,229,0.5)] hover:shadow-[0_0_25px_rgba(79,70,229,0.7)] cursor-pointer">
            Yangi Buyurtma
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* KPI Cards */}
        {[
          { label: "Bugungi Buyurtmalar", value: "24", trend: "+12%", color: "text-emerald-400", icon: "📦" },
          { label: "Faol Xodimlar", value: "15/18", trend: "Band", color: "text-amber-400", icon: "👥" },
          { label: "O'rtacha Baho", value: "4.9", trend: "+0.2", color: "text-emerald-400", icon: "⭐" },
          { label: "AI Muvaffaqiyati", value: "94%", trend: "Avto-yopilgan", color: "text-indigo-400", icon: "🤖" },
        ].map((stat, idx) => (
          <div key={idx} className="glass-card rounded-2xl p-6 transition-all hover:translate-y-[-5px] hover:shadow-[0_15px_40px_rgba(0,0,0,0.4)]">
            <div className="flex justify-between items-start mb-4">
              <p className="text-slate-400 font-medium">{stat.label}</p>
              <span className="text-2xl">{stat.icon}</span>
            </div>
            <div className="flex items-end justify-between">
              <h2 className="text-4xl font-bold text-white">{stat.value}</h2>
              <span className={`text-sm font-semibold px-2 py-1 rounded-md bg-slate-800/50 ${stat.color}`}>
                {stat.trend}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Orders List */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-white">Jonli Navbat (Live)</h3>
            <button className="text-sm text-indigo-400 hover:text-indigo-300">Barchasini ko'rish &rarr;</button>
          </div>
          <div className="space-y-4">
            {[
              { id: "#1042", client: "Sardor K.", service: "Gilam yuvish", status: "Jarayonda", time: "10 daqiqa oldin", platform: "Telegram", worker: "Akmal" },
              { id: "#1043", client: "Malika T.", service: "Uy tozalash", status: "Kutmoqda", time: "2 daqiqa oldin", platform: "Instagram", worker: "Biriktirilmoqda..." },
              { id: "#1044", client: "Otabek", service: "Ofis tozalash", status: "Bajarildi", time: "1 soat oldin", platform: "Web", worker: "Sanjar" },
            ].map((order, i) => (
              <div key={i} className="flex flex-col sm:flex-row justify-between sm:items-center p-4 rounded-xl bg-slate-800/30 border border-slate-700/50 hover:bg-slate-700/40 transition-colors cursor-pointer">
                <div className="flex items-center gap-4 mb-3 sm:mb-0">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold
                    ${order.platform === 'Telegram' ? 'bg-blue-500/20 text-blue-400' : 
                      order.platform === 'Instagram' ? 'bg-pink-500/20 text-pink-400' : 
                      'bg-emerald-500/20 text-emerald-400'}`}>
                    {order.platform.substring(0, 1)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-white flex items-center gap-2">
                      {order.client} <span className="text-xs font-normal text-slate-500">{order.id}</span>
                    </h4>
                    <p className="text-sm text-slate-400">{order.service} • {order.time}</p>
                  </div>
                </div>
                <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center w-full sm:w-auto">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border
                    ${order.status === 'Jarayonda' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 
                      order.status === 'Kutmoqda' ? 'bg-slate-500/10 border-slate-500/20 text-slate-300' : 
                      'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'}`}>
                    {order.status}
                  </span>
                  <p className="text-xs text-slate-500 mt-0 sm:mt-2">Xodim: {order.worker}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Analytics Agent */}
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden flex flex-col h-full">
          {/* Animated background blob for AI feel */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 rounded-full blur-[40px] animate-pulse-glow"></div>
          
          <h3 className="text-xl font-bold text-white mb-6 relative z-10 flex items-center gap-2">
            <span className="text-indigo-400">⚡</span> AI Analitik
          </h3>
          
          <div className="flex-1 space-y-4 relative z-10">
            <div className="p-4 rounded-xl bg-indigo-900/20 border border-indigo-500/30">
              <p className="text-sm text-indigo-200 mb-1 font-medium">Proaktiv Savdo Bashorati</p>
              <p className="text-xs text-slate-300">Bugun yomg'ir yog'ishi sababli "Deraza yuvish" xizmatiga talab 45% pasaydi. "Gilam quritish" reklamasini yoqishni taklif qilaman.</p>
              <button className="mt-3 text-xs bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 py-1.5 px-3 rounded-lg transition-colors border border-indigo-500/30">
                Aksiyani boshlash
              </button>
            </div>
            
            <div className="p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/30">
              <p className="text-sm text-emerald-200 mb-1 font-medium">Logistika Optimizatsiyasi</p>
              <p className="text-xs text-slate-300">3 ta xodim Chilonzor tumanida. Ularga yondosh 2 ta yangi buyurtmani zudlik bilan biriktirdim (Yoqilg'i tejalishi: ~15km).</p>
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-slate-700/50 relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <p className="text-sm text-slate-400">Asal AI (Agent) faol holatda</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
