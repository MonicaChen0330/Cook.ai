// frontend/src/components/student/StudentSidebar.tsx
import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { FaBookOpen, FaPencilAlt, FaCode, FaChartBar, FaChevronLeft } from 'react-icons/fa';

interface StudentSidebarProps {
  courseId?: string;
  isSidebarOpen: boolean; // 接收狀態
  onToggle: () => void;   // 接收切換函式
}

function StudentSidebar({ courseId, isSidebarOpen, onToggle }: StudentSidebarProps) {
  const baseCoursePath = courseId ? `/student/course/${courseId}` : '/student';

  const [isTextVisible, setIsTextVisible] = useState(true);

  useEffect(() => {
    if (isSidebarOpen) {
      const timer = setTimeout(() => {
        setIsTextVisible(true);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setIsTextVisible(false);
    }
  }, [isSidebarOpen]);

  return (
    <aside
      className={`
        bg-white border-r border-gray-200 py-6 flex-shrink-0
        transition-[width] duration-300 ease-in-out h-full
        ${isSidebarOpen ? 'w-64' : 'w-20'} 
      `}
    >
      <div className={`flex flex-col h-full ${isSidebarOpen ? 'px-6' : 'px-2'}`}>

        {/* 標題與收合按鈕區塊 */}
        <div
          className={`
            flex items-center mb-6 
            ${isSidebarOpen ? 'justify-between' : 'justify-center'}
          `}
        >
          {/* 標題：只在開啟且文字可見時顯示 */}
          <h3
            className={`
              text-lg font-bold text-gray-800 whitespace-nowrap overflow-hidden
              transition-opacity duration-150
              ${isTextVisible ? 'opacity-100' : 'opacity-0'}
              ${!isSidebarOpen && 'hidden'}
            `}
          >
            學生功能
          </h3>

          {/* 收合按鈕 */}
          <button
            onClick={onToggle}
            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 flex-shrink-0 focus:outline-none"
            title={isSidebarOpen ? "收起選單" : "展開選單"}
          >
            <FaChevronLeft
              className={`w-5 h-5 transition-transform duration-300 ${!isSidebarOpen && 'rotate-180'}`}
            />
          </button>
        </div>

        <nav>
          <ul className="list-none p-0 m-0 space-y-2">
            {courseId && (
              <>
                <li>
                  <NavLink
                    to={`${baseCoursePath}/materials`}
                    className={({ isActive }) =>
                      `flex items-center h-12 px-4 no-underline rounded-md font-medium transition-all duration-200 ease-in-out
                      ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-blue-500'}
                      ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                      `
                    }
                  >
                    <FaBookOpen className="flex-shrink-0 w-5 h-5" />
                    <span className={`whitespace-nowrap transition-opacity duration-150 ${isTextVisible ? 'opacity-100' : 'opacity-0'} ${!isSidebarOpen && 'hidden'}`}>
                      課程教材
                    </span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to={`${baseCoursePath}/assignments`}
                    className={({ isActive }) =>
                      `flex items-center h-12 px-4 no-underline rounded-md font-medium transition-all duration-200 ease-in-out
                      ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-blue-500'}
                      ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                      `
                    }
                  >
                    <FaPencilAlt className="flex-shrink-0 w-5 h-5" />
                    <span className={`whitespace-nowrap transition-opacity duration-150 ${isTextVisible ? 'opacity-100' : 'opacity-0'} ${!isSidebarOpen && 'hidden'}`}>
                      練習題與作業
                    </span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to={`${baseCoursePath}/coding`}
                    className={({ isActive }) =>
                      `flex items-center h-12 px-4 no-underline rounded-md font-medium transition-all duration-200 ease-in-out
                      ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-blue-500'}
                      ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                      `
                    }
                  >
                    <FaCode className="flex-shrink-0 w-5 h-5" />
                    <span className={`whitespace-nowrap transition-opacity duration-150 ${isTextVisible ? 'opacity-100' : 'opacity-0'} ${!isSidebarOpen && 'hidden'}`}>
                      程式練習
                    </span>
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to={`${baseCoursePath}/dashboard`}
                    className={({ isActive }) =>
                      `flex items-center h-12 px-4 no-underline rounded-md font-medium transition-all duration-200 ease-in-out
                      ${isActive ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-blue-500'}
                      ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                      `
                    }
                  >
                    <FaChartBar className="flex-shrink-0 w-5 h-5" />
                    <span className={`whitespace-nowrap transition-opacity duration-150 ${isTextVisible ? 'opacity-100' : 'opacity-0'} ${!isSidebarOpen && 'hidden'}`}>
                      學習儀表板
                    </span>
                  </NavLink>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default StudentSidebar;