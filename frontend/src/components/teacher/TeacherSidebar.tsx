import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  FaRobot,
  FaDatabase,
  FaClipboardList,
  FaBullhorn,
  FaChartBar,
  FaBook,
  FaUserSecret,
  FaCalculator,
  FaChevronLeft
} from 'react-icons/fa';

interface TeacherSidebarProps {
  courseId?: string;
  isSidebarOpen: boolean;
  onToggle: () => void;
}

function TeacherSidebar({ courseId, isSidebarOpen, onToggle }: TeacherSidebarProps) {
  const courseName = "智慧型網路服務工程"; 
  const baseCoursePath = courseId ? `/teacher/course/${courseId}` : '.';

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
        h-full flex flex-col 
        bg-white border-r border-neutral-border flex-shrink-0 
        transition-[width] duration-300 ease-in-out 
        ${isSidebarOpen ? 'w-50' : 'w-20'}
      `}
    >
      <div 
        className={`
          flex-1 overflow-y-auto 
          ${isSidebarOpen ? 'px-6' : 'px-4'} 
          py-6
        `}
      >
        
        <div 
          className={`
            flex items-center mb-6
            ${isSidebarOpen ? 'justify-between' : 'justify-center'}
          `}
        >
          <h3 
            className={`
              text-lg font-bold text-neutral-text-main
              mr-4
              transition-opacity duration-150
              ${isTextVisible ? 'opacity-100' : 'opacity-0'}
              ${!isSidebarOpen && 'hidden'} 
            `}
          >
            {courseName}
          </h3>

          <button 
            onClick={onToggle} 
            className="p-2 rounded-default text-neutral-icon hover:bg-neutral-background flex-shrink-0"
          >
            <FaChevronLeft 
              className={`w-5 h-5 transition-transform duration-300 ${!isSidebarOpen && 'rotate-180'}`} 
            />
          </button>
        </div>
        
        <nav>
          <ul className="list-none p-0 m-0">
            
            <li>
              <NavLink 
                to={baseCoursePath} 
                end 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaRobot className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  Cook AI 助教
                </span>
              </NavLink>
            </li>
            
            <li>
              <NavLink 
                to={`${baseCoursePath}/materials-db`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaDatabase className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  教材資料庫
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/materials-mgmt`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaClipboardList className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  教材管理
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/announcements`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaBullhorn className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  公告管理
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/students-dashboard`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaChartBar className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  學生儀表板
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/literature-review`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaBook className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  Literature Review
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/ai-detector`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaUserSecret className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  AI Detector
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink 
                to={`${baseCoursePath}/carbon-emission-calculator`} 
                className={({ isActive }) =>
                  `flex items-center h-12 px-4 no-underline rounded-default font-medium transition-colors duration-200 ease-in-out 
                  ${isActive ? 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to text-white' : 'text-neutral-text-secondary hover:bg-neutral-background hover:text-theme-primary'}
                  ${isSidebarOpen ? 'gap-3' : 'justify-center'}
                `
                }
              >
                <FaCalculator className="flex-shrink-0 w-5 h-5" />
                <span 
                  className={`
                    text-sm
                    transition-opacity duration-150
                    ${isTextVisible ? 'opacity-100' : 'opacity-0'}
                    ${!isSidebarOpen && 'hidden'}
                  `}
                >
                  探排計算指標
                </span>
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default TeacherSidebar;