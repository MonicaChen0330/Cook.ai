import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import Spinner from '../common/Spinner';

interface ChatInterfaceProps {
  selectedSourceIds: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ selectedSourceIds }) => {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]); // To store chat history

  const { mutate, isLoading, isError, data, error } = useMutation({
    mutationFn: async ({ query, source_ids }: { query: string; source_ids: string[] }) => {
      const response = await fetch('http://localhost:8000/api/teacher/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, source_ids }),
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }
      return response.json();
    },
    onSuccess: (result) => {
      setChatHistory((prev) => [...prev, { type: 'user', text: query }, { type: 'ai', text: result.response }]);
      setQuery(''); // Clear query after successful response
    },
    onError: (err: any) => {
      setChatHistory((prev) => [...prev, { type: 'user', text: query }, { type: 'error', text: err.message }]);
    },
  });

  const handleSendQuery = () => {
    if (!query.trim()) return;
    if (selectedSourceIds.length === 0) {
      alert('請至少選擇一個來源！');
      return;
    }

    mutate({ query, source_ids: selectedSourceIds });
  };

  return (
    <div className="flex flex-col h-full p-6">
      <div className="flex-shrink-0 pb-4 border-b border-gray-200">
        <h2 className="text-xl font-bold">ICAISS</h2>
        <p className="text-sm text-gray-500">28 個來源</p>
      </div>

      <div className="flex-1 py-4 overflow-y-auto">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`mb-4 ${msg.type === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-3 rounded-lg ${msg.type === 'user' ? 'bg-blue-500 text-white' : msg.type === 'error' ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-800'}`}>
              {msg.text}
            </div>
          </div>
        ))}

        {isLoading && <Spinner />}
        {isError && (
          <div className="p-4 bg-red-100 text-red-700 rounded-lg shadow-sm">
            錯誤: {error?.message || '未知錯誤'}
          </div>
        )}
        {data && (
          <div className="p-4 bg-white rounded-lg shadow-sm">
            <p className="text-gray-700">
              AI 回應: {data.response}
            </p>
          </div>
        )}
      </div>

      <div className="flex-shrink-0 mt-auto">
        <div className="flex p-3 space-x-3 bg-white rounded-lg shadow-sm border border-gray-200">
          <input
            type="text"
            className="flex-1 w-full p-0 border-none focus:ring-0 text-gray-800"
            placeholder="請輸入你的指令，例如：幫我出 10 題選擇題"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendQuery();
              }
            }}
            disabled={isLoading}
          />
          <button
            className="px-5 py-2.5 font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none"
            onClick={handleSendQuery}
            disabled={isLoading}
          >
            傳送
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

