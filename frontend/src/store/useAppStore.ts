import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  name: string
  role: 'admin' | 'worker' | 'client'
}

interface AppState {
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  
  user: User | null
  setUser: (user: User | null) => void
  
  isSidebarOpen: boolean
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'dark', // User requested dark as default in open questions?
      setTheme: (theme) => set({ theme }),
      
      user: null,
      setUser: (user) => set({ user }),
      
      isSidebarOpen: true,
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
    }),
    {
      name: 'tozalash-storage',
      // We only want to persist theme and auth tokens/user
      partialize: (state) => ({ theme: state.theme, user: state.user }),
    }
  )
)
