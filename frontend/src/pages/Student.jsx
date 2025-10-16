import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/common/Header';
import Footer from '../components/common/Footer';

function Student() {
  const [breadcrumbPaths, setBreadcrumbPaths] = useState(null);

  return (
    <div className="page-wrapper">
      <Header paths={breadcrumbPaths} />
      <main className="page-content">
        <Outlet context={{ setBreadcrumbPaths, breadcrumbPaths }} />
      </main>
      <Footer />
    </div>
  );
}

export default Student;