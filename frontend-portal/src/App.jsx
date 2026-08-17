import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Workers from './pages/Workers';
import Analytics from './pages/Analytics';
import Clients from './pages/Clients';
import Settings from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[#09090b] text-slate-100 overflow-hidden relative selection:bg-indigo-500/30">
        {/* Animated Background Elements */}
        <div className="fixed top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 blur-[100px] pointer-events-none mix-blend-screen animate-pulse duration-10000" />
        <div className="fixed bottom-[-10%] left-[-5%] w-[500px] h-[500px] rounded-full bg-purple-500/10 blur-[100px] pointer-events-none mix-blend-screen animate-pulse duration-7000" />
        <div className="fixed top-[40%] left-[20%] w-[300px] h-[300px] rounded-full bg-cyan-500/5 blur-[80px] pointer-events-none mix-blend-screen" />
        
        <Sidebar />
        
        <main className="flex-1 ml-[280px] p-8 h-screen overflow-y-auto relative z-10 custom-scrollbar">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/workers" element={<Workers />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
