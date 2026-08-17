import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import ServicesList from './pages/ServicesList';
import OrderForm from './pages/OrderForm';
import './index.css';

function App() {
  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    
    // Setup theme based on Telegram settings
    if (WebApp.themeParams.bg_color) {
      document.documentElement.style.setProperty('--tg-theme-bg-color', WebApp.themeParams.bg_color);
      document.documentElement.style.setProperty('--tg-theme-text-color', WebApp.themeParams.text_color);
      document.documentElement.style.setProperty('--tg-theme-button-color', WebApp.themeParams.button_color);
      document.documentElement.style.setProperty('--tg-theme-button-text-color', WebApp.themeParams.button_text_color);
    }
  }, []);

  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<ServicesList />} />
          <Route path="/order" element={<OrderForm />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
