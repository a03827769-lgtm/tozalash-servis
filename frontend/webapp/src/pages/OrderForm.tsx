import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import { ArrowLeft, CheckCircle2, MapPin, Calendar, Smartphone, FileText } from 'lucide-react';
import axios from 'axios';

const OrderForm = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const serviceId = searchParams.get('service');
  
  const [formData, setFormData] = useState({
    location: '',
    datetime: '',
    phone: '',
    comment: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    // Fill phone if available from Telegram
    if (WebApp.initDataUnsafe?.user) {
      // Telegram Mini App user info doesn't provide phone directly without request_contact,
      // but we can prepare the UI.
    }
    
    // WebApp Main Button
    WebApp.MainButton.text = "Buyurtma berish";
    WebApp.MainButton.show();
    WebApp.MainButton.onClick(handleSubmit);
    
    return () => {
      WebApp.MainButton.offClick(handleSubmit);
      WebApp.MainButton.hide();
    };
  }, [formData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    if (!formData.location || !formData.datetime || !formData.phone) {
      WebApp.showAlert("Iltimos, manzil, sana va telefon raqamni kiriting.");
      return;
    }
    
    setIsSubmitting(true);
    WebApp.MainButton.showProgress();
    
    try {
      const telegramId = WebApp.initDataUnsafe?.user?.id || '123456789'; // Fallback for local testing
      
      const payload = {
        telegram_id: telegramId.toString(),
        address: formData.location,
        service_type: serviceId,
        planned_time: new Date(formData.datetime).toISOString(),
        total_price: 300000, // Mock price for MVP
      };
      
      // In production, configure exact API URL
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await axios.post(`${apiUrl}/bot/telegram/create_order`, payload);
      
      setIsSuccess(true);
      WebApp.MainButton.hide();
      WebApp.HapticFeedback.notificationOccurred('success');
      
    } catch (error) {
      console.error(error);
      WebApp.showAlert("Xatolik yuz berdi. Iltimos qayta urinib ko'ring.");
    } finally {
      setIsSubmitting(false);
      WebApp.MainButton.hideProgress();
    }
  };

  if (isSuccess) {
    return (
      <div className="animate-fade-in" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <CheckCircle2 size={64} color="var(--accent)" style={{ margin: '0 auto 24px' }} />
        <h2>Buyurtma qabul qilindi!</h2>
        <p style={{ marginBottom: '32px' }}>Operator tez orada siz bilan bog'lanadi va tafsilotlarni tasdiqlaydi.</p>
        <button className="btn-primary" onClick={() => navigate('/')}>
          Bosh sahifaga qaytish
        </button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="header" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            onClick={() => navigate('/')}
            style={{ background: 'none', border: 'none', color: 'var(--text-color)', cursor: 'pointer' }}
          >
            <ArrowLeft size={24} />
          </button>
          <h2 style={{ margin: 0 }}>Buyurtma rasmiylashtirish</h2>
        </div>
      </div>

      <div className="glass glass-card delay-100" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Sparkles size={20} color="var(--primary)" />
          <h3 style={{ margin: 0, fontSize: '18px' }}>Xizmat: {serviceId}</h3>
        </div>
      </div>

      <form className="delay-200 animate-fade-in" style={{ animationDelay: '200ms' }}>
        <div style={{ position: 'relative' }}>
          <MapPin size={20} style={{ position: 'absolute', left: '16px', top: '15px', color: 'rgba(255,255,255,0.5)' }} />
          <input 
            type="text" 
            name="location"
            placeholder="Manzil (Tuman, ko'cha, uy...)"
            value={formData.location}
            onChange={handleChange}
            style={{ paddingLeft: '48px' }}
          />
        </div>

        <div style={{ position: 'relative' }}>
          <Calendar size={20} style={{ position: 'absolute', left: '16px', top: '15px', color: 'rgba(255,255,255,0.5)' }} />
          <input 
            type="datetime-local" 
            name="datetime"
            value={formData.datetime}
            onChange={handleChange}
            style={{ paddingLeft: '48px' }}
          />
        </div>

        <div style={{ position: 'relative' }}>
          <Smartphone size={20} style={{ position: 'absolute', left: '16px', top: '15px', color: 'rgba(255,255,255,0.5)' }} />
          <input 
            type="tel" 
            name="phone"
            placeholder="Telefon raqam (+998...)"
            value={formData.phone}
            onChange={handleChange}
            style={{ paddingLeft: '48px' }}
          />
        </div>

        <div style={{ position: 'relative' }}>
          <FileText size={20} style={{ position: 'absolute', left: '16px', top: '15px', color: 'rgba(255,255,255,0.5)' }} />
          <textarea 
            name="comment"
            placeholder="Qo'shimcha izoh (ixtiyoriy)"
            value={formData.comment}
            onChange={handleChange}
            rows={4}
            style={{ paddingLeft: '48px', resize: 'none' }}
          />
        </div>
      </form>
    </div>
  );
};

export default OrderForm;
