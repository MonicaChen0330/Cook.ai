// frontend/src/pages/Home.jsx
import { Link } from 'react-router-dom';
import { FaChalkboardTeacher, FaUserGraduate } from 'react-icons/fa';
import Footer from '../components/common/Footer'; // 【關鍵修正】確保 Footer 被正確引入
import './Home.css';

function Home() {
  return (
    // 這個 page-wrapper 是將 Footer 推到底部的關鍵
    <div className="page-wrapper">
      <main className="home-container">
        <h1>Cool Knowledge.ai Demo</h1>
        <div className="portal-links">
          <Link to="/teacher" className="portal-card">
            <FaChalkboardTeacher size={50} />
            <h2>教師平台</h2>
            <span>教材生成與課程管理</span>
          </Link>
          <Link to="/student" className="portal-card">
            <FaUserGraduate size={50} />
            <h2>學生平台</h2>
            <span>智慧學習與程式練習</span>
          </Link>
        </div>
      </main>
      <Footer /> {/* 【關鍵修正】將 Footer 元件放在這裡 */}
    </div>
  );
}

export default Home;