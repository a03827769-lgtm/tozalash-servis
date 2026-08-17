import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useRealtimeDashboard } from '../hooks/useRealtimeDashboard';

// Fix leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// A custom dark mode map tile
const DARK_MAP_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

// Center of Tashkent
const TASHKENT_CENTER = [41.2995, 69.2401];

const LiveMap = () => {
  const { workers } = useRealtimeDashboard();
  
  // Fake workers if ws fails
  const displayWorkers = workers && workers.length > 0 ? workers : [
    { id: 'W1', name: 'Aziz', status: 'available', lat: 41.3110, lng: 69.2401 },
    { id: 'W2', name: 'Malika', status: 'busy', lat: 41.2850, lng: 69.2500 },
    { id: 'W3', name: 'Timur', status: 'offline', lat: 41.3000, lng: 69.2100 },
  ];

  return (
    <div className="glass-card" style={{ padding: '0', overflow: 'hidden', height: '400px', borderRadius: '16px' }}>
      <MapContainer center={TASHKENT_CENTER} zoom={12} style={{ height: '100%', width: '100%', background: '#09090b' }}>
        <TileLayer
          url={DARK_MAP_URL}
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        {displayWorkers.map(w => (
          <Marker key={w.id} position={[w.lat, w.lng]}>
            <Popup>
              <div style={{ color: '#000' }}>
                <strong style={{ display: 'block', fontSize: '14px' }}>{w.name}</strong>
                <span style={{ fontSize: '12px', color: w.status === 'available' ? 'green' : w.status === 'busy' ? 'orange' : 'gray' }}>
                  {w.status.toUpperCase()}
                </span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default LiveMap;
