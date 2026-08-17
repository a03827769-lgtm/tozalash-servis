import React from 'react';
import { Save } from 'lucide-react';

const Settings = () => {
  return (
    <div style={{ paddingBottom: '40px', maxWidth: '800px' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 className="heading-xl">Settings</h1>
        <p className="text-muted">Manage system configurations and company details.</p>
      </header>

      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 600, borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>Company Profile</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label className="text-muted" style={{ fontSize: '14px' }}>Company Name</label>
            <input type="text" defaultValue="Tozalash Servis" style={{ 
              padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'inherit', outline: 'none'
            }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label className="text-muted" style={{ fontSize: '14px' }}>Support Email</label>
            <input type="email" defaultValue="support@tozalash.uz" style={{ 
              padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'inherit', outline: 'none'
            }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', gridColumn: '1 / -1' }}>
            <label className="text-muted" style={{ fontSize: '14px' }}>Business Address</label>
            <input type="text" defaultValue="Tashkent, Yunusabad 14-88" style={{ 
              padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'inherit', outline: 'none'
            }} />
          </div>
        </div>

        <h3 style={{ fontSize: '18px', fontWeight: 600, borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px', marginTop: '16px' }}>Preferences</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 500 }}>Email Notifications</div>
              <div className="text-muted" style={{ fontSize: '14px' }}>Receive emails for new orders.</div>
            </div>
            <label style={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
              <input type="checkbox" defaultChecked style={{ width: '20px', height: '20px', accentColor: 'var(--accent-primary)' }} />
            </label>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 500 }}>SMS Alerts</div>
              <div className="text-muted" style={{ fontSize: '14px' }}>Send SMS to clients when workers depart.</div>
            </div>
            <label style={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
              <input type="checkbox" defaultChecked style={{ width: '20px', height: '20px', accentColor: 'var(--accent-primary)' }} />
            </label>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <button className="btn">
            <Save size={18} /> Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
