/* 
主要功能: 
1. 為所有課程內部頁面提供一個包含「學生側邊欄」的兩欄式版面。
2.「中間人」，負責將上層傳遞下來的資料（例如麵包屑的設定工具）繼續傳遞給真正顯示內容的子頁面 
*/

import { Outlet, useOutletContext } from 'react-router-dom';
import StudentSidebar from './StudentSidebar';
import './StudentCourseLayout.css';

function StudentCourseLayout() {
  // 接收從 Student.jsx 傳來的 context
  const context = useOutletContext(); 

  return (
    <div className="portal-body"> 
      <StudentSidebar />
      <main className="portal-content">
        {/* 將接收到的 context 再傳遞給下一層的 Outlet ✨ */}
        <Outlet context={context} /> 
      </main>
    </div>
  );
}

export default StudentCourseLayout;