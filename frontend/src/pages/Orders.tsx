import React, { useState } from 'react'
import { Search, Filter, MoreVertical, Calendar as CalendarIcon, MapPin, CheckCircle, Clock, AlertCircle } from 'lucide-react'

// Dummy ma'lumotlar
const initialOrders = [
  { id: 'ORD-001', client: 'Javohir T.', service: 'Umumiy tozalash', date: '2026-08-14', status: 'bajarildi', amount: '450,000 UZS', location: 'Chilonzor 9-mavze' },
  { id: 'ORD-002', client: 'Malika R.', service: 'Gilam yuvish', date: '2026-08-15', status: 'jarayonda', amount: '120,000 UZS', location: 'Yunusobod 12-daha' },
  { id: 'ORD-003', client: 'Sardor Q.', service: 'Oyna yuvish', date: '2026-08-15', status: 'kutilyapti', amount: '200,000 UZS', location: 'Mirzo Ulugbek' },
  { id: 'ORD-004', client: 'Kamola I.', service: 'Mebel tozalash', date: '2026-08-16', status: 'bekor_qilindi', amount: '350,000 UZS', location: 'Yakkasaroy' },
  { id: 'ORD-005', client: 'Alisher O.', service: 'Umumiy tozalash', date: '2026-08-17', status: 'kutilyapti', amount: '550,000 UZS', location: 'Sergeli 3' },
]

export const Orders = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [sortBy, setSortBy] = useState('date_desc')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'bajarildi':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"><CheckCircle className="w-3 h-3 mr-1" /> Bajarildi</span>
      case 'jarayonda':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800"><Clock className="w-3 h-3 mr-1 animate-pulse" /> Jarayonda</span>
      case 'kutilyapti':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800"><Clock className="w-3 h-3 mr-1" /> Kutilyapti</span>
      case 'bekor_qilindi':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400 border border-rose-200 dark:border-rose-800"><AlertCircle className="w-3 h-3 mr-1" /> Bekor qilindi</span>
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700">Noma'lum</span>
    }
  }

  let filteredOrders = initialOrders.filter(order => {
    const matchesSearch = order.client.toLowerCase().includes(searchTerm.toLowerCase()) || order.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || order.status === filterStatus
    return matchesSearch && matchesStatus
  })

  // Sorting
  filteredOrders = filteredOrders.sort((a, b) => {
    if (sortBy === 'date_desc') return new Date(b.date).getTime() - new Date(a.date).getTime()
    if (sortBy === 'date_asc') return new Date(a.date).getTime() - new Date(b.date).getTime()
    if (sortBy === 'amount_desc') return parseInt(b.amount.replace(/\D/g,'')) - parseInt(a.amount.replace(/\D/g,''))
    if (sortBy === 'amount_asc') return parseInt(a.amount.replace(/\D/g,'')) - parseInt(b.amount.replace(/\D/g,''))
    return 0
  })

  // Pagination
  const totalPages = Math.ceil(filteredOrders.length / itemsPerPage)
  const paginatedOrders = filteredOrders.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  return (
    <div className="p-6 md:p-8 space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white">Buyurtmalar</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Barcha mijoz buyurtmalarini boshqarish va filtrlash</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
            <span className="text-xl leading-none">+</span> Yangi buyurtma
          </button>
        </div>
      </div>

      {/* Tools / Filters */}
      <div className="glass bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 p-4 rounded-xl flex flex-col sm:flex-row gap-4 shadow-sm backdrop-blur-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input 
            type="text" 
            placeholder="Mijoz ismi yoki ID orqali qidirish..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-shadow"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="text-gray-400 w-5 h-5 hidden sm:block" />
          <select 
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full sm:w-48 px-3 py-2 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white cursor-pointer"
          >
            <option value="all">Barcha holatlar</option>
            <option value="kutilyapti">Kutilyapti</option>
            <option value="jarayonda">Jarayonda</option>
            <option value="bajarildi">Bajarildi</option>
            <option value="bekor_qilindi">Bekor qilindi</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full sm:w-48 px-3 py-2 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white cursor-pointer"
          >
            <option value="date_desc">Sana (Eng yangi)</option>
            <option value="date_asc">Sana (Eng eski)</option>
            <option value="amount_desc">Summa (Kattadan)</option>
            <option value="amount_asc">Summa (Kichikdan)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700/50 rounded-xl shadow-sm overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700/50">
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Buyurtma ID</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Mijoz</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Xizmat</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sana / Manzil</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Holat</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider text-right">Summa</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider text-center">Amal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700/50">
              {paginatedOrders.length > 0 ? paginatedOrders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/20 transition-colors group">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900 dark:text-white">{order.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-sm mr-3">
                        {order.client.charAt(0)}
                      </div>
                      <span className="font-medium text-gray-700 dark:text-gray-200">{order.client}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-300">{order.service}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-1">
                      <span className="flex items-center text-sm text-gray-600 dark:text-gray-300"><CalendarIcon className="w-3.5 h-3.5 mr-1" /> {order.date}</span>
                      <span className="flex items-center text-xs text-gray-400 dark:text-gray-500"><MapPin className="w-3.5 h-3.5 mr-1" /> {order.location}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(order.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-gray-900 dark:text-white">
                    {order.amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-gray-400 dark:text-gray-500">
                    <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    Hech narsa topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Jami: <span className="font-medium text-gray-900 dark:text-white">{filteredOrders.length}</span> ta
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md disabled:opacity-50"
              >
                Oldingi
              </button>
              <div className="flex items-center px-2 text-sm text-gray-600 dark:text-gray-300">
                Sahifa {currentPage} / {totalPages}
              </div>
              <button 
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md disabled:opacity-50"
              >
                Keyingi
              </button>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  )
}
