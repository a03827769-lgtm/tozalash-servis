import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShoppingCart, Users, UserCircle, LineChart, Settings, Bot } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'AI Dispatcher', path: '/orders', icon: Bot },
    { name: 'Fleet', path: '/workers', icon: Users },
    { name: 'Clients', path: '/clients', icon: UserCircle },
    { name: 'Analytics', path: '/analytics', icon: LineChart },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="fixed inset-y-0 left-0 w-[280px] bg-black/40 backdrop-blur-2xl border-r border-white/5 p-6 flex flex-col z-50 transition-all">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-[0_0_20px_rgba(99,102,241,0.5)]">
          T
        </div>
        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 m-0">Tozalash AI</h2>
      </div>

      <nav className="flex flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 relative overflow-hidden group ${
                isActive 
                  ? 'text-white bg-indigo-500/10 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.15)] font-medium' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent font-normal'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500 ${isActive ? 'opacity-100' : 'opacity-0'}`} />
                <item.icon size={20} className={`relative z-10 ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span className="relative z-10">{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-6 border-t border-white/10">
        <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors cursor-pointer">
          <div className="relative">
            <img src="https://ui-avatars.com/api/?name=Admin+User&background=6366f1&color=fff" alt="Admin" className="w-10 h-10 rounded-full" />
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-[#09090b] rounded-full"></div>
          </div>
          <div>
            <div className="font-medium text-sm text-slate-200">System Admin</div>
            <div className="text-xs text-slate-500">admin@tozalash.ai</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
