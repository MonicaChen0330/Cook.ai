import React, { useState } from 'react';
// 稍後我們將建立這兩個新組件
import SourcePanel from './SourcePanel';
import ChatInterface from './ChatInterface';

// 假設這是你的 Source 資料結構 (你未來會從 API 取得)
export type Source = {
  id: string; // 唯一的 UUID
  name: string; // 顯示的檔案名稱
};

const TeacherAICenter: React.FC = () => {
  // 1. 狀態：管理來源面板是否開啟，預設為 true
  const [isPanelOpen, setIsPanelOpen] = useState(true);

  // 2. 狀態：管理老師勾選了哪些來源 (儲存 ID)
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  // 模擬的來源資料 (之後請替換成 API 呼叫)
  const DUMMY_SOURCES: Source[] = [
    { id: 'uuid-source-1', name: '1_Agentic_AI_Autonomo...' },
    { id: 'uuid-source-2', name: '2_Viability_into_AI_Agent...' },
    { id: 'uuid-source-3', name: '3_AGENTPEERTALK_Em...' },
    { id: 'uuid-source-4', name: '6_Agentic_Systems_A_Gu...' },
  ];

  // 處理來源勾選的函式
  const handleSelectSource = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId) // 如果已經選了，就取消
        : [...prev, sourceId] // 否則就加入
    );
  };

  return (
    // -----  這裡是主要的修改點 -----
    // 1. 加上 "bg-white"：這會把整個底色變成你想要的乾淨白色
    // 2. 加上 "p-4" (padding)：在整個容器周圍加上一點邊距
    // 3. 加上 "space-x-4"：在 SourcePanel 和 ChatInterface 之間創造間距
    <div className="flex w-full h-full p-4 space-x-4 bg-white">
      
      {/* 1. 來源面板 (SourcePanel) */}
      {/* 我們仍然傳遞 props，但 SourcePanel 稍後需要被修改，
        讓它變成一個有 'shadow' 和 'rounded-lg' 的浮動卡片
      */}
      <SourcePanel
        isOpen={isPanelOpen}
        onToggle={() => setIsPanelOpen(!isPanelOpen)}
        availableSources={DUMMY_SOURCES}
        selectedSources={selectedSources}
        onSelectSource={handleSelectSource}
      />

      {/* 2. 聊天介面 (ChatInterface) */}
      {/* flex-1 讓它自動填滿所有剩餘空間 */}
      {/* min-w-0 解決 flex 內容溢出的問題 */}
      <main className="flex-1 h-full min-w-0">
        <ChatInterface 
          selectedSourceIds={selectedSources} 
        />
      </main>
    </div>
  );
};

export default TeacherAICenter;
