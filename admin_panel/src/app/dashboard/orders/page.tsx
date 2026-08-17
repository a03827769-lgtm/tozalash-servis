"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, MoreVertical, Edit2, Trash2 } from "lucide-react";
import { api } from "@/lib/api";

interface Order {
  id: string | number;
  order_number: string;
  client_name: string;
  client_phone: string;
  service_name: string;
  total_price: number;
  status: string;
  scheduled_date: string;
  created_at: string;
}

export default function OrdersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [ordersList, setOrdersList] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const response = await api.get('/orders');
        setOrdersList(response.data);
      } catch (error) {
        console.error("Failed to fetch orders", error);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);
  
  const filteredOrders = ordersList.filter(o => 
    o.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    o.client_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Buyurtmalar Tarixi</h1>
          <p className="text-slate-400 text-sm mt-1">Jami: {ordersList.length} ta buyurtma</p>
        </div>
        <button className="btn-primary px-4 py-2 rounded-xl text-sm font-medium">
          Yangi Buyurtma
        </button>
      </div>

      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Buyurtma ID yoki Mijoz ismi..." 
            className="glass-input w-full pl-10 pr-4 py-2 rounded-xl text-sm"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="glass-input px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-slate-300 w-full md:w-auto justify-center">
            <Filter className="w-4 h-4" />
            Holat
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
                <th className="px-6 py-4 font-medium">Mijoz</th>
                <th className="px-6 py-4 font-medium">Sana</th>
                <th className="px-6 py-4 font-medium">Holat</th>
                <th className="px-6 py-4 font-medium">Mas'ul xodim</th>
                <th className="px-6 py-4 font-medium">Summa</th>
                <th className="px-6 py-4 font-medium text-right">Amal</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order, index) => (
                <motion.tr 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  key={order.id} 
                  className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-blue-400">{order.order_number}</td>
                  <td className="px-6 py-4">{order.client_name}</td>
                  <td className="px-6 py-4 text-slate-300">{new Date(order.scheduled_date || order.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      order.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 
                      order.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                      order.status === 'cancelled' ? 'bg-rose-500/20 text-rose-400' :
                      'bg-orange-500/20 text-orange-400'
                    }`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">{order.service_name}</td>
                  <td className="px-6 py-4 font-medium text-emerald-400">{order.total_price?.toLocaleString('uz-UZ') || 0} UZS</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-blue-400 transition-colors">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-rose-400 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
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
