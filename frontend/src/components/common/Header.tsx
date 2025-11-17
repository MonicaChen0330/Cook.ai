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
    // header底線
    <header className="h-[60px] bg-white border-b border-neutral-border px-8 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-6">
        {/* Cook.ai Logo */}
        <div className="
          text-2xl 
          font-extrabold
          bg-gradient-to-r 
          from-theme-gradient-deep
          via-theme-gradient-middle
          to-theme-gradient-light
          text-transparent bg-clip-text
        ">
          Cook.ai
        </div>

        {/* 如果 paths 存在，就顯示 Breadcrumb 元件 */}
        {paths && paths.length > 0 && <Breadcrumb paths={paths} />}
      </div>
      <div className="flex items-center gap-4">

        {/* 使用者名稱 */}
        <span className="text-neutral-text-secondary">{userName}</span>

        {/* 登出按鈕 */}
        <button 
          className="
            bg-destructive text-white border-none py-2 px-4 
            rounded-default
            cursor-pointer transition-colors 
            hover:bg-destructive-hover
            focus:outline-none focus:ring-2 focus:ring-destructive focus:ring-offset-2
          "
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Header;