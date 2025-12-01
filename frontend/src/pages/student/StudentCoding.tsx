import { useEffect } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';

// 定義 Context 型別，與 Layout 保持一致
interface OutletContext {
    setBreadcrumbPaths: React.Dispatch<React.SetStateAction<Array<{ name: string; path: string }> | null>>;
    breadcrumbPaths: Array<{ name: string; path: string }> | null;
}

const StudentCoding = () => {
    const { courseId } = useParams();
    const context = useOutletContext<OutletContext>();

    useEffect(() => {
        // 設定麵包屑導航：學生總覽 > 課程名稱 > 程式練習
        if (context.setBreadcrumbPaths && courseId) {
            context.setBreadcrumbPaths([
                { name: '學生總覽', path: '/student' },
                { name: '課程', path: `/student/course/${courseId}` }, // 這一層讓使用者可以點回去
                { name: '程式練習', path: `/student/course/${courseId}/coding` } // 當前頁面
            ]);
        }
    }, [courseId, context.setBreadcrumbPaths]);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">程式練習</h2>
            </div>

            {/* 這裡放置主要的程式練習介面內容 */}
            <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 min-h-[400px]">
                <p className="text-gray-500 mb-4">
                    此區塊為程式練習介面 (Coding Playground or IDE integration)。
                </p>
                <div className="p-4 bg-gray-50 rounded border border-gray-200">
                    <code>Console.log("Hello Cook.ai Student!");</code>
                </div>
            </div>
        </div>
    );
};

export default StudentCoding;