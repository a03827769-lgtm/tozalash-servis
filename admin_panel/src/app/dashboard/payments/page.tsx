"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Filter, ArrowUpRight, ArrowDownRight, CreditCard, DollarSign } from "lucide-react";

const DUMMY_PAYMENTS = Array.from({ length: 12 }).map((_, i) => ({
  id: `PAY-${5000 + i}`,
  client: `Mijoz ${Math.floor(Math.random() * 50) + 1}`,
  date: `2026-08-${(i % 30 + 1).toString().padStart(2, '0')} 14:30`,
  method: ['Payme', 'Click', 'Naqd'][i % 3],
  amount: `${(Math.random() * 1.5 + 0.1).toFixed(1)}M UZS`,
  status: i % 5 === 0 ? 'Kutilmoqda' : 'Tasdiqlandi',
  type: i % 4 === 0 ? 'Qaytarildi' : 'Kirim',
}));

export default function PaymentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  
  const filteredPayments = DUMMY_PAYMENTS.filter(p => 
    p.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.client.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">To'lovlar Tarixi</h1>
          <p className="text-slate-400 text-sm mt-1">Barcha kirim va chiqim operatsiyalari</p>
        </div>
        <button className="btn-primary px-4 py-2 rounded-xl text-sm font-medium">
          Hisobot (Excel)
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-6 rounded-2xl flex items-center gap-4">
          <div className="p-4 bg-emerald-500/10 rounded-xl">
            <ArrowUpRight className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <p className="text-slate-400 text-sm">Umumiy Kirim (Oylik)</p>
            <p className="text-2xl font-bold text-slate-100">45.2M UZS</p>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel p-6 rounded-2xl flex items-center gap-4">
          <div className="p-4 bg-rose-500/10 rounded-xl">
            <ArrowDownRight className="w-8 h-8 text-rose-400" />
          </div>
          <div>
            <p className="text-slate-400 text-sm">Qaytarilgan to'lovlar</p>
            <p className="text-2xl font-bold text-slate-100">1.5M UZS</p>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-panel p-6 rounded-2xl flex items-center gap-4">
          <div className="p-4 bg-blue-500/10 rounded-xl">
            <CreditCard className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <p className="text-slate-400 text-sm">Kutilayotgan (Hold)</p>
            <p className="text-2xl font-bold text-slate-100">3.2M UZS</p>
          </div>
        </motion.div>
      </div>

      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="To'lov ID yoki Mijoz ismi..." 
            className="glass-input w-full pl-10 pr-4 py-2 rounded-xl text-sm"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="glass-input px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-slate-300 w-full md:w-auto justify-center">
            <Filter className="w-4 h-4" />
            Tizim bo'yicha
          </button>
        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-panel rounded-2xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-slate-800/50 border-b border-slate-700/50">
              <tr>
                <th className="px-6 py-4 font-medium">Tranzaksiya ID</th>
                <th className="px-6 py-4 font-medium">Sana va Vaqt</th>
                <th className="px-6 py-4 font-medium">Mijoz</th>
                <th className="px-6 py-4 font-medium">To'lov Tizimi</th>
                <th className="px-6 py-4 font-medium">Summa</th>
                <th className="px-6 py-4 font-medium">Holat</th>
              </tr>
            </thead>
            <tbody>
              {filteredPayments.map((payment, index) => (
                <motion.tr 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + index * 0.05 }}
                  key={payment.id} 
                  className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-slate-300">{payment.id}</td>
                  <td className="px-6 py-4 text-slate-400">{payment.date}</td>
                  <td className="px-6 py-4">{payment.client}</td>
                  <td className="px-6 py-4 text-slate-300 flex items-center gap-2">
                    {payment.method === 'Payme' ? <div className="w-2 h-2 rounded-full bg-cyan-400" /> :
                     payment.method === 'Click' ? <div className="w-2 h-2 rounded-full bg-blue-500" /> :
                     <div className="w-2 h-2 rounded-full bg-emerald-500" />}
                    {payment.method}
                  </td>
                  <td className={`px-6 py-4 font-medium ${payment.type === 'Kirim' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {payment.type === 'Kirim' ? '+' : '-'}{payment.amount}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      payment.status === 'Tasdiqlandi' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'
                    }`}>
                      {payment.status}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
