import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import Spinner from '../common/Spinner';
import { ReportContainer } from '../reports/ReportContainer'; // Import ReportContainer
import Fab from '@mui/material/Fab'; // Import Fab
import SendIcon from '@mui/icons-material/Send'; // Import SendIcon
import StopIcon from '@mui/icons-material/Stop'; // 引入 StopIcon
import { useRef } from 'react';

interface ChatInterfaceProps {
  selectedUniqueContentIds: number[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ selectedUniqueContentIds }) => {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]); // To store chat history
  const abortControllerRef = useRef<AbortController | null>(null); // Declare abortControllerRef

  const { mutate, isPending, isError, data, error } = useMutation({
    mutationFn: async ({ prompt, unique_content_id, user_id }: { prompt: string; unique_content_id: number; user_id: number }) => {
      // Create a new AbortController for each mutation
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await fetch('http://140.115.54.162:8000/api/v1/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ prompt, unique_content_id, user_id }),
          signal: controller.signal, // Pass the signal to fetch
        });

        if (!response.ok) {
          throw new Error('Failed to get AI response');
        }
        return response.json();
      } catch (e: any) {
        if (e.name === 'AbortError') {
          console.log('Fetch aborted by user');
          return { aborted: true }; // Return a custom object to distinguish from other errors/success
        } else {
          throw e; // Re-throw other errors
        }
      } finally {
        // Clear the abort controller ref after the mutation finishes (success, error, or abort)
        abortControllerRef.current = null;
      }
    },
    onSuccess: (apiResponse) => {
      if (apiResponse && 'aborted' in apiResponse && apiResponse.aborted) { // Check for the aborted flag
        setChatHistory((prev) => [...prev, { type: 'info', text: 'AI 生成已取消' }]);
        return; // Don't proceed with success logic
      }
      setChatHistory((prev) => [...prev, { type: 'ai', content: apiResponse.result }]);
      // setQuery(''); // query is already cleared in handleSendQuery
    },
    onError: (err: any) => {
      // Only show error if it's not an AbortError (which is handled in mutationFn's catch)
      if (err.name !== 'AbortError') {
        setChatHistory((prev) => [...prev, { type: 'error', text: err.message }]);
      }
    },
    onSettled: () => {
      // Ensure abortControllerRef is cleared even if mutation fails
      abortControllerRef.current = null;
    }
  });

  const handleSendQuery = () => {
    if (!query.trim()) return;
    if (selectedUniqueContentIds.length === 0) {
      alert('請至少選擇一個參考資料！');
      return;
    }

    // If there's an ongoing request, abort it before starting a new one
    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        setChatHistory((prev) => [...prev, { type: 'info', text: '正在取消先前的 AI 生成...' }]);
    }

    // Immediately add user's query to chat history for better UX
    setChatHistory((prev) => [...prev, { type: 'user', text: query }]);
    const currentQuery = query; // Capture current query before clearing

    setQuery(''); // Clear query input field immediately

    const uniqueContentIdToSend = selectedUniqueContentIds[0];
    console.log('Sending unique_content_id:', uniqueContentIdToSend);

    if (uniqueContentIdToSend === undefined || uniqueContentIdToSend === null || uniqueContentIdToSend === 0) {
        alert('選取的來源出錯!');
        return;
    }

    mutate({ prompt: currentQuery, unique_content_id: uniqueContentIdToSend, user_id: 1 });

    // Alert if more than one source is selected, as backend only processes one.
    if (selectedUniqueContentIds.length > 1) {
        alert('注意：後端目前僅處理第一個選取的來源。');
    }
  };

  return (
    <div className="flex flex-col h-full p-6">

      <div className="flex-1 py-4 overflow-y-auto">
        {chatHistory.map((msg, index) => {
          if (msg.type === 'user') {
            return (
              <div key={index} className="mb-4 text-right">
                <div className="inline-block p-3 rounded-lg bg-blue-600 text-white">
                  {msg.text}
                </div>
              </div>
            );
                    } else if (msg.type === 'ai') {
                      const apiResult = msg.content;
          
                      const shouldRender = () => {
                      console.log('shouldRender check: apiResult =', apiResult); // 添加日誌
          
                      if (!apiResult || !apiResult.display_type) {
                          console.log('shouldRender: apiResult or display_type is missing');
                          return false;
                      }
          
                      if (apiResult.display_type === 'text_message') {
                          const messageText = apiResult.content;
                          const isValidMessage = typeof messageText === 'string' && messageText.trim().length > 0;
                          console.log('shouldRender: text_message, messageText =', messageText, 'isValidMessage =', isValidMessage);
                          return isValidMessage;
                      }
          
                      if (apiResult.display_type === 'exam_questions' || apiResult.display_type === 'summary_report') {
                          const data = apiResult.content.data || apiResult.content;
                          const isValidData = (Array.isArray(data) && data.length > 0) || (typeof data === 'object' && data !== null && Object.keys(data).length > 0);
                          console.log('shouldRender: exam_questions/summary_report, isValidData =', isValidData);
                          return isValidData;
                      }
          
                      console.log('shouldRender: unknown type, rendering by default');
                      return true; // 對於其他未知類型，預設渲染
                      };
          
                      const doRender = shouldRender(); // 呼叫 shouldRender 並儲存結果
                      console.log(`ChatInterface: msg.type 'ai' - shouldRender returned: ${doRender} for apiResult:`, apiResult); // 添加日誌
          
                      if (!doRender) { // 使用儲存的結果
                          return null; // 如果不應該渲染，則返回 null
                      }
          
                      console.log('ChatInterface: Rendering ReportContainer for apiResult:', apiResult); // 添加日誌
          
                      return (
                        <div key={index} className="mb-4 text-left">
                          <ReportContainer result={msg.content} />
                        </div>
                      );
                    } else if (msg.type === 'error') {
            return (
              <div key={index} className="mb-4 text-left">
                <div className="p-3 bg-red-200 text-red-800 rounded-lg">
                  錯誤: {msg.text}
                </div>
              </div>
            );
          } else if (msg.type === 'info') { // Added for abortion message
            return (
              <div key={index} className="mb-4 text-center text-sm text-neutral-text-secondary">
                {msg.text}
              </div>
            );
          }
          return null;
        })}

        {isPending && <Spinner />}
        {isError && (
          <div className="p-4 bg-red-100 text-red-700 rounded-lg shadow-sm">
            錯誤: {error?.message || '未知錯誤'}
          </div>
        )}
      </div>

      <div className="flex-shrink-0 mt-auto">
              {/* 🎯 修正：垂直置中和輸入框 padding */}
              <div className="flex items-center px-3 py-2 space-x-3 bg-white rounded-lg shadow-sm border border-gray-200">
                <input
                  type="text"
                  // 修正：給予垂直 padding 讓輸入框佔據足夠空間並使文字置中
                  className="flex-1 w-full py-3 border-none focus:ring-0 text-gray-800"
                  placeholder="請輸入你的指令，例如：幫我出 10 題選擇題"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendQuery();
                    }
                  }}
                  disabled={isPending}
                />
                {/* 🎯 修正：按鈕狀態切換 */}
                <Fab 
                  color={isPending ? "default" : "primary"} // Change color to gray when pending
                  aria-label="傳送" 
                  onClick={isPending ? () => abortControllerRef.current?.abort() : handleSendQuery} // Abort or send
                  disabled={!query.trim() && !isPending} 
                  size="medium" 
                  sx={{ boxShadow: 'none' }} 
                >
                  {isPending ? <StopIcon /> : <SendIcon />} {/* Change icon to StopIcon */}
                </Fab>
              </div>      </div>

    </div>
  );
};

export default ChatInterface;

