"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Users, 
  User,
  Briefcase, 
  CalendarCheck, 
  CreditCard,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Buyurtmalar", href: "/dashboard/orders", icon: CalendarCheck },
    { name: "Xodimlar", href: "/dashboard/staff", icon: Briefcase },
    { name: "Mijozlar", href: "/dashboard/clients", icon: Users },
    { name: "To'lovlar", href: "/dashboard/payments", icon: CreditCard },
    { name: "Sozlamalar", href: "/dashboard/settings", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100 flex overflow-hidden">
      {/* Sidebar */}
      <motion.aside 
        initial={false}
        animate={{ width: isSidebarOpen ? 280 : 0, opacity: isSidebarOpen ? 1 : 0 }}
        className="glass-panel border-y-0 border-l-0 z-20 flex-shrink-0 relative overflow-hidden"
      >
        <div className="w-[280px] h-full flex flex-col p-6">
          <div className="flex items-center gap-3 mb-10 mt-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              Tozalash Servis
            </h2>
          </div>

          <nav className="flex-1 space-y-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.name} href={item.href}>
                  <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 relative group ${isActive ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
                    {isActive && (
                      <motion.div 
                        layoutId="activeTab"
                        className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.15)]"
                      />
                    )}
                    <item.icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-blue-400' : 'group-hover:text-blue-400 transition-colors'}`} />
                    <span className="font-medium relative z-10">{item.name}</span>
                  </div>
                </Link>
              );
            })}
          </nav>

          <div className="pt-6 border-t border-slate-700/50 mt-auto">
            <button className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-red-400 transition-colors w-full rounded-xl hover:bg-red-500/10">
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Chiqish</span>
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <header className="h-20 glass-panel border-x-0 border-t-0 flex items-center justify-between px-8 z-10 relative">
          <button 
            onClick={() => setSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 p-[2px]">
              <div className="w-full h-full bg-slate-900 rounded-full flex items-center justify-center border border-slate-800">
                <User className="w-5 h-5 text-slate-300" />
              </div>
            </div>
            <div className="hidden md:block text-sm">
              <p className="font-medium text-slate-200">Super Admin</p>
              <p className="text-slate-400 text-xs">admin@tozalash.uz</p>
            </div>
          </div>
        </header>
        
        <div className="flex-1 overflow-y-auto p-8 relative z-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] -z-10 pointer-events-none" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px] -z-10 pointer-events-none" />
          {children}
        </div>
      </main>
    </div>
  );
}
