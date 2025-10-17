import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/common/Header';
import Footer from '../components/common/Footer.tsx';

// Define the type for a single breadcrumb path item
interface BreadcrumbPath {
  name: string;
  path: string;
}

// Define the type for the Outlet context
interface OutletContext {
  setBreadcrumbPaths: React.Dispatch<React.SetStateAction<BreadcrumbPath[] | null>>;
  breadcrumbPaths: BreadcrumbPath[] | null;
}

function Student() {
  const [breadcrumbPaths, setBreadcrumbPaths] = useState<BreadcrumbPath[] | null>(null);

  return (
    <div className="page-wrapper">
      <Header paths={breadcrumbPaths} />
      <main className="page-content">
        <Outlet context={{ setBreadcrumbPaths, breadcrumbPaths } as OutletContext} />
      </main>
      <Footer />
    </div>
  );
}

export default Student;