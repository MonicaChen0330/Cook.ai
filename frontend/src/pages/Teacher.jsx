// frontend/src/pages/Teacher.jsx
import { useState } from 'react'; // 引入 useState
import { Outlet } from 'react-router-dom';
import Header from '../components/common/Header';
import Footer from '../components/common/Footer';

function Teacher() {
  // 建立 state 來管理麵包屑
  const [breadcrumbPaths, setBreadcrumbPaths] = useState(null);

  return (
    <div className="page-wrapper">
      <Header paths={breadcrumbPaths} />
      <main className="page-content">
        {/* 將 state 和 setter 傳遞下去 */}
        <Outlet context={{ setBreadcrumbPaths, breadcrumbPaths }} />
      </main>
      <Footer />
    </div>
  );
}

export default Teacher;