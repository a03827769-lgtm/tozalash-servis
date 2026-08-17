"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, MoreVertical, Edit2, Trash2, Star, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

interface Staff {
  id: string | number;
  name: string;
  role: string;
  phone: string;
  status: string;
  rating: string | number;
  completedTasks: number;
}

export default function StaffPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStaff = async () => {
      try {
        const response = await api.get('/staff');
        // Map the backend data to frontend format
        // Backend returns: [{id, user_id, user: {full_name, role, phone}, status, rating, completed_tasks}]
        // Let's assume standard response based on models
        setStaffList(response.data);
      } catch (error) {
        console.error("Failed to fetch staff", error);
      } finally {
        setLoading(false);
      }
    };
    fetchStaff();
  }, []);
  
  const filteredStaff = staffList.filter(s => 
    s.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    s.role?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Xodimlar</h1>
          <p className="text-slate-400 text-sm mt-1">Jami: {staffList.length} ta xodim</p>
        </div>
        <button className="btn-primary px-4 py-2 rounded-xl text-sm font-medium">
          Yangi Xodim
        </button>
      </div>

      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Xodim ismi yoki lavozimi..." 
            className="glass-input w-full pl-10 pr-4 py-2 rounded-xl text-sm"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="glass-input px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-slate-300 w-full md:w-auto justify-center">
            <Filter className="w-4 h-4" />
            Lavozim
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
                <th className="px-6 py-4 font-medium">Lavozim</th>
                <th className="px-6 py-4 font-medium">Telefon</th>
                <th className="px-6 py-4 font-medium">Holat</th>
                <th className="px-6 py-4 font-medium">Reyting</th>
                <th className="px-6 py-4 font-medium text-right">Amal</th>
              </tr>
            </thead>
            <tbody>
              {filteredStaff.map((staff, index) => (
                <motion.tr 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  key={staff.id} 
                  className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-blue-400">{staff.id}</td>
                  <td className="px-6 py-4">{staff.name}</td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-1 text-slate-300">
                      {staff.role === 'Admin' && <ShieldCheck className="w-4 h-4 text-rose-400" />}
                      {staff.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">{staff.phone}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      staff.status === 'Band emas' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'
                    }`}>
                      {staff.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-1 text-yellow-400 font-medium">
                      <Star className="w-4 h-4 fill-current" />
                      {staff.rating}
                    </span>
                  </td>
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
