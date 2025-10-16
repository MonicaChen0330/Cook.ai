// frontend/src/components/student/StudentSidebar.jsx
import { NavLink } from 'react-router-dom';
import { FaBook, FaCode, FaChartBar } from 'react-icons/fa';
import './StudentSidebar.css';

function StudentSidebar() {
  return (
    <aside className="student-sidebar">
      <div className="sidebar-section">
        <h3 className="section-title">學生功能</h3>
        <nav>
          <ul>
            <li><NavLink to="/student/learning"><FaBook /> 學習輔助</NavLink></li>
            <li><NavLink to="/student/coding"><FaCode /> 程式練習</NavLink></li>
            <li><NavLink to="/student/dashboard"><FaChartBar /> 學習儀表板</NavLink></li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default StudentSidebar;