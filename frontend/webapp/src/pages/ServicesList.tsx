import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, Sofa, Sparkles, Building2, Wind, ArrowRight } from 'lucide-react';

const services = [
  { id: 'standart', title: 'Standart Tozalash', desc: 'Odatiy uyni tozalash va tartibga keltirish', icon: Home, price: '300,000' },
  { id: 'chuqur', title: 'Chuqur Tozalash', desc: 'Barcha burchaklar va qiyin joylarni tozalash', icon: Sparkles, price: '600,000' },
  { id: 'remontdan_keyin', title: 'Ta\'mirdan keyin', desc: 'Qurilish changlari va qoldiqlarni tozalash', icon: Building2, price: '800,000' },
  { id: 'klyner', title: 'Mebel/Gilam yuvish', desc: 'Yumshoq mebellar va gilamlarni yuvish', icon: Sofa, price: '150,000' },
  { id: 'oyna', title: 'Oyna yuvish', desc: 'Deraza va oynalarni yaltiratib yuvish', icon: Wind, price: '100,000' }
];

const ServicesList = () => {
  const navigate = useNavigate();

  const handleSelect = (serviceId: string) => {
    navigate(`/order?service=${serviceId}`);
  };

  return (
    <div className="animate-fade-in">
      <div className="header">
        <div>
          <h1>Tozalash Servis</h1>
          <p>Bizning xizmatlarimiz</p>
        </div>
      </div>

      <div className="grid-2">
        {services.map((service, index) => {
          const Icon = service.icon;
          return (
            <div 
              key={service.id} 
              className={`glass glass-card delay-${(index + 1) * 100}`}
              onClick={() => handleSelect(service.id)}
              style={{ cursor: 'pointer', padding: '20px' }}
            >
              <div className="service-icon">
                <Icon size={24} />
              </div>
              <h3 style={{ fontSize: '16px' }}>{service.title}</h3>
              <p style={{ fontSize: '13px', marginBottom: '12px', minHeight: '40px' }}>{service.desc}</p>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600', color: 'var(--primary)' }}>{service.price} so'm</span>
                <ArrowRight size={16} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServicesList;
