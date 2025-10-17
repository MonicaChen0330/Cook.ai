// frontend/src/components/teacher/TeacherSidebar.jsx
import { NavLink } from 'react-router-dom';
import { 
  FaRobot,          // AI 助教
  FaDatabase,       // 資料庫
  FaClipboardList,  // 任務/管理列表
  FaBullhorn,       // 公告
  FaChartBar        // 圖表/儀表板
} from 'react-icons/fa';

interface TeacherSidebarProps {
  courseId?: string; // Keep courseId prop if it's used elsewhere for context
}

function TeacherSidebar({ courseId }: TeacherSidebarProps) {
  const courseName = "智慧型網路服務工程"; // Original course name
  const baseCoursePath = courseId ? `/teacher/course/${courseId}` : '.'; // Adjust base path for NavLink

  return (
    <aside className="w-72 bg-white border-r border-gray-200 py-6 flex-shrink-0">
      <div className="px-6">
        <h3 className="text-lg font-bold text-gray-800 mb-6 px-4">{courseName}</h3>
        <nav>
          <ul className="list-none p-0 m-0">
            <li>
              <NavLink 
                to={baseCoursePath} 
                end 
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaRobot /> Cook AI 助教
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/materials-db`} 
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaDatabase /> 教材資料庫
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/materials-mgmt`} 
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaClipboardList /> 教材管理
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/announcements`} 
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaBullhorn /> 公告管理
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/students-dashboard`} 
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaChartBar /> 學生儀表板
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default TeacherSidebar;