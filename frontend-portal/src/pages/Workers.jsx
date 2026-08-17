import React from 'react';
import { Star, MapPin, Phone, Mail } from 'lucide-react';

const mockWorkers = [
  { id: 1, name: 'Rustam Djalilov', role: 'Senior Cleaner', rating: 4.9, jobs: 124, status: 'On Duty', avatar: 'https://ui-avatars.com/api/?name=Rustam+D&background=6366f1&color=fff' },
  { id: 2, name: 'Alisher Botirov', role: 'Specialist', rating: 4.7, jobs: 89, status: 'Available', avatar: 'https://ui-avatars.com/api/?name=Alisher+B&background=8b5cf6&color=fff' },
  { id: 3, name: 'Feruza Tursunova', role: 'Cleaner', rating: 4.8, jobs: 210, status: 'Off Duty', avatar: 'https://ui-avatars.com/api/?name=Feruza+T&background=06b6d4&color=fff' },
  { id: 4, name: 'Dilshod Karim', role: 'Supervisor', rating: 5.0, jobs: 340, status: 'Available', avatar: 'https://ui-avatars.com/api/?name=Dilshod+K&background=ec4899&color=fff' },
  { id: 5, name: 'Madina Umarova', role: 'Cleaner', rating: 4.6, jobs: 45, status: 'On Duty', avatar: 'https://ui-avatars.com/api/?name=Madina+U&background=facc15&color=fff' },
  { id: 6, name: 'Jasur N.', role: 'Cleaner', rating: 4.5, jobs: 32, status: 'Available', avatar: 'https://ui-avatars.com/api/?name=Jasur+N&background=22c55e&color=fff' },
];

const Workers = () => {
  return (
    <div style={{ paddingBottom: '40px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 className="heading-xl">Workers</h1>
          <p className="text-muted">Manage your cleaning staff and monitor their status.</p>
        </div>
        <button className="btn">Add New Worker</button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        {mockWorkers.map((worker) => (
          <div key={worker.id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <img src={worker.avatar} alt={worker.name} style={{ width: '60px', height: '60px', borderRadius: '16px' }} />
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600 }}>{worker.name}</h3>
                  <p className="text-muted" style={{ fontSize: '14px' }}>{worker.role}</p>
                </div>
              </div>
              <div className={`badge ${worker.status === 'Available' ? 'success' : worker.status === 'On Duty' ? 'info' : 'warning'}`}>
                {worker.status === 'On Duty' && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor' }}></span>}
                {worker.status}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--glass-border)', borderBottom: '1px solid var(--glass-border)', padding: '12px 0', marginTop: '8px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#facc15', fontWeight: 600 }}>
                  <Star size={16} fill="currentColor" /> {worker.rating}
                </div>
                <div className="text-muted" style={{ fontSize: '12px', marginTop: '4px' }}>Rating</div>
              </div>
              <div style={{ width: '1px', background: 'var(--glass-border)' }}></div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 600 }}>{worker.jobs}</div>
                <div className="text-muted" style={{ fontSize: '12px', marginTop: '4px' }}>Jobs Done</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button style={{ flex: 1, padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', justifyContent: 'center' }}>
                <Phone size={18} />
              </button>
              <button style={{ flex: 1, padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', justifyContent: 'center' }}>
                <Mail size={18} />
              </button>
              <button style={{ flex: 2, padding: '8px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '8px', color: 'var(--accent-primary)', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', fontWeight: 500 }}>
                <MapPin size={18} /> View Location
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Workers;
