import { useState, FormEvent } from 'react';

interface RegisterFormProps {
  onSuccess?: (message: string) => void;
  onError?: (error: string) => void;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
  student_id: string;
  major?: string;
  enrollment_year?: number;
}

interface RegisterResponse {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  message: string;
}

export default function RegisterForm({ onSuccess, onError }: RegisterFormProps) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    student_id: '',
    major: '',
    enrollment_year: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 驗證 Email 格式
  const validateEmail = (email: string): boolean => {
    return email.includes('@gmail.com');
  };

  // 驗證表單
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Email 驗證
    if (!formData.email) {
      newErrors.email = 'Email 為必填欄位';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Email 必須使用 Gmail (@gmail.com)';
    }

    // 密碼驗證
    if (!formData.password) {
      newErrors.password = '密碼為必填欄位';
    } else if (formData.password.length < 6) {
      newErrors.password = '密碼至少需要 6 個字元';
    }

    // 確認密碼驗證
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '密碼不一致';
    }

    // 姓名驗證
    if (!formData.full_name) {
      newErrors.full_name = '姓名為必填欄位';
    }

    // 學號驗證
    if (!formData.student_id) {
      newErrors.student_id = '學號為必填欄位';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 處理表單提交
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const registerData: RegisterData = {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        student_id: formData.student_id,
        major: formData.major || undefined,
        enrollment_year: formData.enrollment_year ? parseInt(formData.enrollment_year) : undefined,
        role: 'student',
      };

      console.log('發送註冊請求:', registerData);

      // NOTE: Port is set to 8001 because 8000 is currently occupied.
      // If you are another developer using this registration function,
      // please manually change the port from 8001 back to 8000 if needed.
      // 直接呼叫 API
      const response = await fetch('http://127.0.0.1:8001/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData),
      });

      console.log('收到回應:', response.status, response.statusText);

      if (!response.ok) {
        const error = await response.json();
        console.error('註冊失敗:', error);
        throw new Error(error.detail || '註冊失敗');
      }

      const result: RegisterResponse = await response.json();
      console.log('註冊成功:', result);
      
      if (onSuccess) {
        onSuccess(result.message || '註冊成功！');
      }

      // 清空表單
      setFormData({
        email: '',
        password: '',
        confirmPassword: '',
        full_name: '',
        student_id: '',
        major: '',
        enrollment_year: '',
      });
    } catch (error) {
      console.error('捕獲錯誤:', error);
      const errorMessage = error instanceof Error ? error.message : '註冊失敗，請稍後再試';
      if (onError) {
        onError(errorMessage);
      }
      setErrors({ submit: errorMessage });
    } finally {
      console.log('設定 isSubmitting = false');
      setIsSubmitting(false);
    }
  };

  // 處理輸入變化
  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除該欄位的錯誤訊息
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          Email <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          id="email"
          value={formData.email}
          onChange={(e) => handleChange('email', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
            errors.email
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          }`}
          placeholder="your.email@gmail.com"
          disabled={isSubmitting}
        />
        {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
      </div>

      {/* 密碼 */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
          密碼 <span className="text-red-500">*</span>
        </label>
        <input
          type="password"
          id="password"
          value={formData.password}
          onChange={(e) => handleChange('password', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
            errors.password
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          }`}
          placeholder="至少 6 個字元"
          disabled={isSubmitting}
        />
        {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
      </div>

      {/* 確認密碼 */}
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
          確認密碼 <span className="text-red-500">*</span>
        </label>
        <input
          type="password"
          id="confirmPassword"
          value={formData.confirmPassword}
          onChange={(e) => handleChange('confirmPassword', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
            errors.confirmPassword
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          }`}
          placeholder="再次輸入密碼"
          disabled={isSubmitting}
        />
        {errors.confirmPassword && (
          <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
        )}
      </div>

      {/* 姓名 */}
      <div>
        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
          姓名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="full_name"
          value={formData.full_name}
          onChange={(e) => handleChange('full_name', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
            errors.full_name
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          }`}
          placeholder="請輸入真實姓名"
          disabled={isSubmitting}
        />
        {errors.full_name && <p className="text-red-500 text-sm mt-1">{errors.full_name}</p>}
      </div>

      {/* 學號 */}
      <div>
        <label htmlFor="student_id" className="block text-sm font-medium text-gray-700 mb-1">
          學號 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="student_id"
          value={formData.student_id}
          onChange={(e) => handleChange('student_id', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
            errors.student_id
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          }`}
          placeholder="例如：109123456"
          disabled={isSubmitting}
        />
        {errors.student_id && <p className="text-red-500 text-sm mt-1">{errors.student_id}</p>}
      </div>

      {/* 科系 (選填) */}
      <div>
        <label htmlFor="major" className="block text-sm font-medium text-gray-700 mb-1">
          科系 <span className="text-gray-400 text-xs">(選填)</span>
        </label>
        <input
          type="text"
          id="major"
          value={formData.major}
          onChange={(e) => handleChange('major', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="例如：資訊工程系"
          disabled={isSubmitting}
        />
      </div>

      {/* 入學年份 (選填) */}
      <div>
        <label htmlFor="enrollment_year" className="block text-sm font-medium text-gray-700 mb-1">
          入學年份 <span className="text-gray-400 text-xs">(選填)</span>
        </label>
        <input
          type="number"
          id="enrollment_year"
          value={formData.enrollment_year}
          onChange={(e) => handleChange('enrollment_year', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="例如：109"
          min="100"
          max="120"
          disabled={isSubmitting}
        />
      </div>

      {/* 錯誤訊息 */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {errors.submit}
        </div>
      )}

      {/* 提交按鈕 */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all ${
          isSubmitting
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to hover:shadow-lg hover:-translate-y-0.5'
        }`}
      >
        {isSubmitting ? '註冊中...' : '註冊'}
      </button>
    </form>
  );
}
