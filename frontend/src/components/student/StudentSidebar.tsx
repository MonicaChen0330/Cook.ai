// frontend/src/components/student/StudentSidebar.jsx
import { NavLink } from 'react-router-dom';
import { FaHome, FaBook, FaChalkboardTeacher, FaCog } from 'react-icons/fa';

interface StudentSidebarProps {
  courseId?: string;
}

function StudentSidebar({ courseId }: StudentSidebarProps) {
  const baseCoursePath = courseId ? `/student/course/${courseId}` : '/student';

  return (
    <aside className="w-72 bg-white border-r border-gray-200 py-6 flex-shrink-0">
      <div className="px-6">
        <h3 className="text-lg font-bold text-gray-800 mb-6 px-4">學生功能</h3>
        <nav>
          <ul className="list-none p-0 m-0">
            <li>
              <NavLink
                to="/student"
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
                end
              >
                <FaHome />
                <span>儀表板</span>
              </NavLink>
            </li>
            {courseId && (
              <>
                <li>
                  <NavLink
                    to={baseCoursePath}
                    className={({ isActive }) =>
                      `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                    }
                    end
                  >
                    <FaBook />
                    <span>課程總覽</span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to={`${baseCoursePath}/materials`}
                    className={({ isActive }) =>
                      `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                    }
                  >
                    <FaChalkboardTeacher />
                    <span>教材與作業</span>
                  </NavLink>
                </li>
              </>
            )}
            <li>
              <NavLink
                to="/student/settings"
                className={({ isActive }) =>
                  `flex items-center gap-3 py-3 px-4 no-underline rounded-md text-gray-600 font-medium transition-all duration-200 ease-in-out ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'hover:bg-gray-100 hover:text-blue-500'}`
                }
              >
                <FaCog />
                <span>設定</span>
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default StudentSidebar;