import React from 'react';

const mockClients = [
  { id: 1, name: 'Aziz Rakhimov', email: 'aziz@example.com', phone: '+998 90 123 45 67', orders: 12, totalSpent: '5,400,000 UZS', status: 'Active' },
  { id: 2, name: 'Malika Tursunova', email: 'malika.t@example.com', phone: '+998 91 987 65 43', orders: 4, totalSpent: '1,200,000 UZS', status: 'Active' },
  { id: 3, name: 'Timur Karimov', email: 'timur_k@example.com', phone: '+998 93 456 78 90', orders: 1, totalSpent: '800,000 UZS', status: 'Inactive' },
  { id: 4, name: 'Nigina Saydullaeva', email: 'nigina99@example.com', phone: '+998 99 321 09 87', orders: 8, totalSpent: '3,100,000 UZS', status: 'Active' },
];

const Clients = () => {
  return (
    <div style={{ paddingBottom: '40px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 className="heading-xl">Clients Database</h1>
          <p className="text-muted">Manage your customer relationships.</p>
        </div>
        <button className="btn">Add Client</button>
      </header>

      <div className="glass-card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left' }}>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Client Name</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Contact Info</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Total Orders</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Total Spent</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {mockClients.map((client) => (
              <tr key={client.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                <td style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                      {client.name.charAt(0)}
                    </div>
                    <span style={{ fontWeight: 500 }}>{client.name}</span>
                  </div>
                </td>
                <td style={{ padding: '16px' }}>
                  <div>{client.phone}</div>
                  <div className="text-muted" style={{ fontSize: '12px' }}>{client.email}</div>
                </td>
                <td style={{ padding: '16px' }}>{client.orders}</td>
                <td style={{ padding: '16px', fontWeight: 500 }}>{client.totalSpent}</td>
                <td style={{ padding: '16px' }}>
                  <span className={`badge ${client.status === 'Active' ? 'success' : 'warning'}`}>
                    {client.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Clients;
