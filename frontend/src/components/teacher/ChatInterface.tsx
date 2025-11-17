import React, { useState } from 'react';
// 之後你會在這裡導入 React Query 的 useMutation
// import { useMutation } from 'react-query'; 
// 還有你的 QuestionList 組件
// import QuestionList from './QuestionList';

interface ChatInterfaceProps {
  selectedSourceIds: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ selectedSourceIds }) => {
  const [query, setQuery] = useState('');
  
  // 這裡就是你呼叫 API 的地方
  const handleSendQuery = () => {
    if (!query.trim()) return; // 防止空查詢
    if (selectedSourceIds.length === 0) {
      alert('請至少選擇一個來源！');
      return;
    }

    console.log('準備呼叫 API ...');
    console.log('Query:', query);
    console.log('Source IDs:', selectedSourceIds);

    // 
    // TODO: 在這裡實作你的 React Query useMutation
    // mutate({ query, sources: selectedSourceIds });
    //
    
    setQuery(''); // 清空輸入框
  };

  return (
    // h-full 搭配 flex-col 讓聊天介面填滿父層高度
    <div className="flex flex-col h-full p-6">
      
      {/* 標題和你的 AI 圖示 (從你的截圖中推測) */}
      <div className="flex-shrink-0 pb-4 border-b border-gray-200">
        <h2 className="text-xl font-bold">ICAISS</h2>
        <p className="text-sm text-gray-500">28 個來源</p>
      </div>

      {/* 聊天/結果顯示區域 */}
      {/* flex-1 讓它佔滿中間所有空間, overflow-y-auto 讓它自己滾動 */}
      <div className="flex-1 py-4 overflow-y-auto">
        
        {/* TODO: 這裡是你渲染生成結果的地方
          
          if (isLoading) return <Spinner />;
          if (isError) return <Error />;
          if (data) return <QuestionList questionData={data} />;
        */}

        <div className="p-4 bg-white rounded-lg shadow-sm">
          <p className="text-gray-700">
            這裡是 AI 聊天和題目生成結果的顯示區域。
            <br/>
            (你昨天的 `QuestionList` 組件將會被渲染在這裡)
          </p>
          <p className="mt-4 text-xs text-gray-400">
            (Debug: 目前選擇的來源: {selectedSourceIds.join(', ') || '無'})
          </p>
        </div>

      </div>

      {/* 輸入框 (Query Input) */}
      <div className="flex-shrink-0 mt-auto">
        {/* 把它包在一個白底、圓角、有陰影的卡片裡 */}
        <div className="flex p-3 space-x-3 bg-white rounded-lg shadow-sm border border-gray-200">
          <input 
            type="text" 
            className="flex-1 w-full p-0 border-none focus:ring-0 text-gray-800" // 移除 input 預設樣式
            placeholder="請輸入你的指令，例如：幫我出 10 題選擇題"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendQuery();
              }
            }}
          />
          <button 
            className="px-5 py-2.5 font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none" // 微調 padding
            onClick={handleSendQuery}
          >
            傳送
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
