// frontend/src/components/teacher/TeacherSidebar.jsx
import { NavLink } from 'react-router-dom';
// ✨ 1. 引入一組新的、更具代表性的圖示
import { 
  FaRobot,          // AI 助教
  FaDatabase,       // 資料庫
  FaClipboardList,  // 任務/管理列表
  FaBullhorn,       // 公告
  FaChartBar        // 圖表/儀表板
} from 'react-icons/fa';
import './TeacherSidebar.css';

function TeacherSidebar() {
  const courseName = "智慧型網路服務工程";

  return (
    <aside className="course-sidebar">
        <div className="sidebar-section">
            <h3 className="section-title">{courseName}</h3>
            <nav>
                <ul>
                    {/* ✨ 2. 將圖示與功能一一對應 */}
                    <li><NavLink to="." end><FaRobot /> Cook AI 助教</NavLink></li>
                    <li><NavLink to="materials-db"><FaDatabase /> 教材資料庫</NavLink></li>
                    <li><NavLink to="materials-mgmt"><FaClipboardList /> 教材管理</NavLink></li>
                    <li><NavLink to="announcements"><FaBullhorn /> 公告管理</NavLink></li>
                    <li><NavLink to="students-dashboard"><FaChartBar /> 學生儀表板</NavLink></li>
                </ul>
            </nav>
        </div>
    </aside>
  );
}

export default TeacherSidebar;