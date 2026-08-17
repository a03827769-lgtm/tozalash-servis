import React, { useState } from 'react';
import { Search, Filter, Eye, MoreVertical, X } from 'lucide-react';

const mockOrders = [
  { id: 'ORD-1041', client: 'Aziz R.', service: 'Deep Clean', date: '2026-08-11', amount: '450,000 UZS', status: 'In Progress', worker: 'Rustam D.' },
  { id: 'ORD-1042', client: 'Malika T.', service: 'Standard', date: '2026-08-12', amount: '200,000 UZS', status: 'Pending', worker: 'Unassigned' },
  { id: 'ORD-1043', client: 'Timur K.', service: 'Move in/out', date: '2026-08-10', amount: '800,000 UZS', status: 'Completed', worker: 'Alisher B.' },
  { id: 'ORD-1044', client: 'Nigina S.', service: 'Post-construction', date: '2026-08-13', amount: '1,200,000 UZS', status: 'Pending', worker: 'Unassigned' },
  { id: 'ORD-1045', client: 'Davron M.', service: 'Standard', date: '2026-08-11', amount: '250,000 UZS', status: 'Cancelled', worker: 'N/A' },
];

const Orders = () => {
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredOrders = mockOrders.filter(order => 
    order.client.toLowerCase().includes(searchTerm.toLowerCase()) || 
    order.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ paddingBottom: '40px', position: 'relative' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 className="heading-xl">Orders Management</h1>
          <p className="text-muted">View and manage all cleaning service requests.</p>
        </div>
        <button className="btn">Create New Order</button>
      </header>

      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '250px', maxWidth: '400px' }}>
            <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} size={18} />
            <input 
              type="text" 
              placeholder="Search by ID or Client..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px 10px 40px', 
                background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)',
                borderRadius: '8px', color: 'var(--text-primary)', outline: 'none',
                fontFamily: 'inherit'
              }} 
            />
          </div>
          <button style={{ 
            background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
            padding: '10px 16px', borderRadius: '8px', color: 'var(--text-primary)',
            display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer'
          }}>
            <Filter size={18} /> Filter Status
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left' }}>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Order ID</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Client</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Service</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Date</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Status</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Amount</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                  <td style={{ padding: '16px', fontWeight: 500 }}>{order.id}</td>
                  <td style={{ padding: '16px' }}>{order.client}</td>
                  <td style={{ padding: '16px' }}>{order.service}</td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{order.date}</td>
                  <td style={{ padding: '16px' }}>
                    <span className={`badge ${order.status === 'Completed' ? 'success' : order.status === 'In Progress' ? 'info' : order.status === 'Pending' ? 'warning' : 'danger'}`}>
                      {order.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px', fontWeight: 500 }}>{order.amount}</td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                      <Eye size={18} style={{ cursor: 'pointer' }} onClick={() => setSelectedOrder(order)} />
                      <MoreVertical size={18} style={{ cursor: 'pointer' }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {selectedOrder && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '32px', position: 'relative' }}>
            <button onClick={() => setSelectedOrder(null)} style={{
              position: 'absolute', top: '16px', right: '16px', background: 'transparent',
              border: 'none', color: 'var(--text-secondary)', cursor: 'pointer'
            }}>
              <X size={24} />
            </button>
            <h2 className="heading-lg" style={{ marginBottom: '8px' }}>Order Details</h2>
            <p className="text-muted" style={{ marginBottom: '24px' }}>{selectedOrder.id}</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Client:</span>
                <span style={{ fontWeight: 500 }}>{selectedOrder.client}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Service:</span>
                <span style={{ fontWeight: 500 }}>{selectedOrder.service}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Status:</span>
                <span className={`badge ${selectedOrder.status === 'Completed' ? 'success' : selectedOrder.status === 'In Progress' ? 'info' : selectedOrder.status === 'Pending' ? 'warning' : 'danger'}`}>
                  {selectedOrder.status}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Assigned Worker:</span>
                <span style={{ fontWeight: 500 }}>{selectedOrder.worker}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Amount:</span>
                <span style={{ fontWeight: 600, fontSize: '18px', color: 'var(--accent-primary)' }}>{selectedOrder.amount}</span>
              </div>
            </div>
            <div style={{ marginTop: '32px', display: 'flex', gap: '12px' }}>
              <button className="btn" style={{ flex: 1, justifyContent: 'center' }}>Edit Order</button>
              <button className="btn" style={{ flex: 1, justifyContent: 'center', background: 'rgba(255,255,255,0.1)' }}>Print Invoice</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
