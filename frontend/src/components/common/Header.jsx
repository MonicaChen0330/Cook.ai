import { useNavigate } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';
import './Header.css';

function Header({ paths }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/'); 
  };

  const userName = "陳淳瑜"; 

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="logo">Cook.ai</div>
        {/* 如果 paths 存在，就顯示 Breadcrumb 元件 */}
        {paths && paths.length > 0 && <Breadcrumb paths={paths} />}
      </div>
      <div className="user-info">
        <span>{userName}</span>
        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

export default Header;