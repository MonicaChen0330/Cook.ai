// frontend/src/components/teacher/FileUpload.tsx

import React, { useState } from 'react';
import { FaUpload } from 'react-icons/fa';
import Button from '../common/Button';

interface FileUploadProps {
  onUploadSuccess: () => void; // Define the prop
}

function FileUpload({ onUploadSuccess }: FileUploadProps) { // Destructure the prop
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
      setMessage('');
    }
  };

  // This function now just returns a promise, as the Button component expects.
  const handleUpload = async () => {
    if (!file) {
      // We can set a message and the Button component will show its error state.
      setMessage('Please select a file first.');
      throw new Error('Please select a file first.');
    }

    setMessage(''); // Clear previous messages
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/api/ingest', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      // Set a detailed error message and throw an error for the Button component
      setMessage(`Error: ${data.detail || 'Upload failed'}`);
      throw new Error(data.detail || 'Upload failed');
    }

    // On success, we can set a success message.
    setMessage(`Success! File ingested with ID: ${data.unique_content_id}`);
    
    // Call the refresh function passed from the parent
    onUploadSuccess();

    // The Button component will handle its own 'success' state.
  };

  return (
    // Removed inline style for cleaner integration
    <div>
      <input type="file" onChange={handleFileChange} className="mb-2 block w-full text-sm text-neutral-text-main file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-theme-primary-light file:text-theme-primary hover:file:bg-theme-primary-lighter" />
      <Button
        variant="primary"
        size="md"
        // The Button component now manages its own state. We no longer pass `buttonState`.
        onClick={handleUpload} // Pass the promise-returning function
        idleText={
          <span className="flex items-center gap-2">
            <FaUpload className="w-4 h-4" /> 上傳檔案
          </span>
        }
        loadingText="上傳中..."
        successText="上傳成功！"
        errorText="上傳失敗"
        className="w-full"
        disabled={!file} // Disable if no file is selected
      />
      {/* The message state is now used for success/error details */}
      {message && <p className="text-sm mt-2">{message}</p>}
    </div>
  );
}

export default FileUpload;
