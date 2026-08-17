"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, MoreVertical, Edit2, Trash2, Mail, Phone } from "lucide-react";
import { api } from "@/lib/api";

interface Client {
  id: string | number;
  name: string;
  phone: string;
  total_orders: number;
  total_spent: number;
  last_activity: string;
  status: string;
}

export default function ClientsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [clientsList, setClientsList] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await api.get('/clients');
        setClientsList(response.data.map((c: any) => ({
          ...c,
          status: c.total_orders > 0 ? "Faol" : "Yangi"
        })));
      } catch (error) {
        console.error("Failed to fetch clients", error);
      } finally {
        setLoading(false);
      }
    };
    fetchClients();
  }, []);
  
  const filteredClients = clientsList.filter(c => 
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.phone?.includes(searchTerm)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Mijozlar Bazasi</h1>
          <p className="text-slate-400 text-sm mt-1">Jami: {clientsList.length} ta mijoz</p>
        </div>
        <button className="btn-primary px-4 py-2 rounded-xl text-sm font-medium">
          Mijoz qo'shish
        </button>
      </div>

      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Mijoz ismi yoki raqami..." 
            className="glass-input w-full pl-10 pr-4 py-2 rounded-xl text-sm"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="glass-input px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-slate-300 w-full md:w-auto justify-center">
            <Filter className="w-4 h-4" />
            Filtrlash
          </button>
        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-2xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-slate-800/50 border-b border-slate-700/50">
              <tr>
                <th className="px-6 py-4 font-medium">ID</th>
                <th className="px-6 py-4 font-medium">F.I.SH.</th>
                <th className="px-6 py-4 font-medium">Telefon</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Buyurtmalar</th>
                <th className="px-6 py-4 font-medium">LTV</th>
                <th className="px-6 py-4 font-medium text-right">Amal</th>
              </tr>
            </thead>
            <tbody>
              {filteredClients.map((client, index) => (
                <motion.tr 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  key={client.id} 
                  className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-blue-400">{client.id}</td>
                  <td className="px-6 py-4">{client.name}</td>
                  <td className="px-6 py-4 text-slate-300">{client.phone}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      client.status === 'VIP' ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-500/20 text-slate-300'
                    }`}>
                      {client.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">{client.total_orders}</td>
                  <td className="px-6 py-4 font-medium text-emerald-400">{client.total_spent.toLocaleString('uz-UZ')} UZS</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-blue-400 transition-colors">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-rose-400 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Dummy */}
        <div className="p-4 border-t border-slate-700/50 flex items-center justify-between text-sm text-slate-400">
          <span>Ko'rsatilmoqda: 1-15 (Jami 45)</span>
          <div className="flex gap-2">
            <button className="px-3 py-1 glass-input rounded-lg hover:bg-slate-700">&lt;</button>
            <button className="px-3 py-1 bg-blue-500 text-white rounded-lg">1</button>
            <button className="px-3 py-1 glass-input rounded-lg hover:bg-slate-700">2</button>
            <button className="px-3 py-1 glass-input rounded-lg hover:bg-slate-700">3</button>
            <button className="px-3 py-1 glass-input rounded-lg hover:bg-slate-700">&gt;</button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
