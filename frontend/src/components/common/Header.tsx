import { useNavigate } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';

// Define the type for the paths prop
interface HeaderProps {
  paths: Array<{ name: string; path: string }> | null;
}

function Header({ paths }: HeaderProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/'); 
  };

  const userName = "陳淳瑜"; 

  return (
    <header className="h-[60px] bg-white border-b border-gray-200 px-8 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-6">
        <div className="text-2xl font-bold bg-primary-gradient text-transparent bg-clip-text">Cook.ai</div>
        {/* 如果 paths 存在，就顯示 Breadcrumb 元件 */}
        {paths && paths.length > 0 && <Breadcrumb paths={paths} />}
      </div>
      <div className="flex items-center gap-4">
        <span>{userName}</span>
        <button 
          className="bg-red-500 text-white border-none py-2 px-4 rounded cursor-pointer transition-colors hover:bg-red-700"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Header;