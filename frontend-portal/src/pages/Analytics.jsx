import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const monthlyRev = [
  { name: 'Jan', revenue: 45 },
  { name: 'Feb', revenue: 52 },
  { name: 'Mar', revenue: 38 },
  { name: 'Apr', revenue: 65 },
  { name: 'May', revenue: 58 },
  { name: 'Jun', revenue: 80 },
  { name: 'Jul', revenue: 95 },
];

const ordersTrend = [
  { name: 'Week 1', orders: 120 },
  { name: 'Week 2', orders: 145 },
  { name: 'Week 3', orders: 110 },
  { name: 'Week 4', orders: 180 },
];

const retentionData = [
  { name: 'Returning', value: 65 },
  { name: 'New Clients', value: 35 },
];
const COLORS = ['#8b5cf6', '#6366f1'];

const Analytics = () => {
  return (
    <div style={{ paddingBottom: '40px' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 className="heading-xl">Analytics Overview</h1>
        <p className="text-muted">In-depth insights into your business performance.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        <div className="glass-card">
          <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '24px' }}>Monthly Revenue (Millions UZS)</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyRev}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
                <YAxis stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ background: 'rgba(5,5,5,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '24px' }}>Orders Trend (This Month)</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ordersTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
                <YAxis stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'rgba(5,5,5,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Line type="monotone" dataKey="orders" stroke="#8b5cf6" strokeWidth={4} dot={{ r: 6, fill: '#8b5cf6', stroke: '#09090b', strokeWidth: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '24px' }}>Client Retention</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={retentionData} cx="50%" cy="50%" innerRadius={80} outerRadius={110} paddingAngle={5} dataKey="value">
                  {retentionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'rgba(5,5,5,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', marginTop: '16px' }}>
            {retentionData.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '4px', background: COLORS[idx] }}></div>
                <span>{item.name} ({item.value}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
