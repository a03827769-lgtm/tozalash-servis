import React from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAppStore } from '@/store/useAppStore'
import { LayoutDashboard, Map as MapIcon, MessageSquare, Calendar as CalendarIcon, Menu, Moon, Sun, LogOut, ClipboardList } from 'lucide-react'

const navItems = [
  { name: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: 'Buyurtmalar', path: '/orders', icon: <ClipboardList className="w-5 h-5" /> },
  { name: 'Xarita', path: '/map', icon: <MapIcon className="w-5 h-5" /> },
  { name: 'Chat', path: '/chat', icon: <MessageSquare className="w-5 h-5" /> },
  { name: 'Taqvim', path: '/calendar', icon: <CalendarIcon className="w-5 h-5" /> },
]

export const MainLayout = () => {
  const { isSidebarOpen, toggleSidebar, theme, setTheme } = useAppStore()
  const location = useLocation()

  return (
    <div className={`min-h-screen flex ${theme === 'dark' ? 'dark' : ''}`}>
      <div className="flex-1 flex flex-col md:flex-row bg-background text-foreground transition-colors duration-300">
        
        {/* Sidebar */}
        <aside className={`${isSidebarOpen ? 'w-64' : 'w-20'} bg-white/10 dark:bg-black/20 backdrop-blur-md border-r border-border transition-all duration-300 flex flex-col`}>
          <div className="h-16 flex items-center justify-between px-4 border-b border-border">
            {isSidebarOpen && <span className="font-bold text-lg text-primary tracking-wide">Tozalash Servis</span>}
            <button onClick={toggleSidebar} className="p-2 rounded-md hover:bg-white/10 transition-colors">
              <Menu className="w-6 h-6" />
            </button>
          </div>
          
          <nav className="flex-1 py-6 flex flex-col gap-2 px-3">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-3 py-3 rounded-lg transition-all ${
                    isActive 
                      ? 'bg-primary text-primary-foreground shadow-md' 
                      : 'hover:bg-white/10 text-muted-foreground hover:text-foreground'
                  }`}
                  title={!isSidebarOpen ? item.name : undefined}
                >
                  <div className={isActive ? 'text-primary-foreground' : ''}>{item.icon}</div>
                  {isSidebarOpen && <span className="ml-3 font-medium">{item.name}</span>}
                </Link>
              )
            })}
          </nav>

          <div className="p-4 border-t border-border flex flex-col gap-4">
            <button 
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="flex items-center p-2 w-full rounded-lg hover:bg-white/10 transition-colors text-muted-foreground hover:text-foreground"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              {isSidebarOpen && <span className="ml-3">Mavzuni o'zgartirish</span>}
            </button>
            <button className="flex items-center p-2 w-full rounded-lg hover:bg-red-500/10 text-red-500 transition-colors">
              <LogOut className="w-5 h-5" />
              {isSidebarOpen && <span className="ml-3">Chiqish</span>}
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[url('/bg-pattern.svg')] bg-cover bg-fixed">
          {/* Topbar / Header if needed, or directly Outlet */}
          <div className="flex-1 overflow-y-auto p-2">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
