// frontend/src/components/teacher/TeacherAICenter.jsx
import { FaSearch, FaYoutube, FaFileAlt, FaEnvelope } from 'react-icons/fa';
import './TeacherAICenter.css';

function TeacherAICenter() {
  const userName = "Ms. Chen"; // 假資料

  return (
    <div className="ai-command-center">
      <div className="welcome-message">
        <div className="sparkle-icon">✨</div>
        <h2>嗨 {userName}，您需要甚麼教學上的幫助?</h2>
      </div>

      <div className="prompt-container">
        <FaSearch className="prompt-icon" />
        <input type="text" placeholder="輸入您的指令製作教材或查詢任何問題..." />
      </div>

      <div className="suggestion-chips">
        <button className="chip"><FaFileAlt /> 產生隨堂練習</button>
        <button className="chip"><FaEnvelope /> 撰寫公告並發送郵件給學生</button>
        <button className="chip"><FaYoutube /> 根據教學影片內容出題</button>
      </div>
    </div>
  );
}

export default TeacherAICenter;