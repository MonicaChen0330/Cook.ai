import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* 用 BrowserRouter 將 App 元件包起來 */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);