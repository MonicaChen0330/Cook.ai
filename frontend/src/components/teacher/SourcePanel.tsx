import React, { useState } from 'react';
import { FaEdit, FaPlus, FaUpload, FaLink } from 'react-icons/fa'; 
import FileUpload from './FileUpload';
import { Source } from './TeacherAICenter';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Box from '@mui/material/Box';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';

interface SourcePanelProps {
  availableSources: Source[];
  selectedSources: string[];
  onSelectSource: (id: string) => void;
  onUploadSuccess: () => void;
}

function SourcePanel({
  availableSources,
  selectedSources,
  onSelectSource,
  onUploadSuccess
}: SourcePanelProps) {
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newName, setNewName] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'file' | 'link'>('file');

  const handleStartEditing = (source: Source) => {
    setEditingId(source.id);
    setNewName(source.name);
  };

  const handleCancelEditing = () => {
    setEditingId(null);
    setNewName('');
  };

  const handleRename = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingId || !newName.trim()) {
      handleCancelEditing();
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/materials/${editingId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newName }),
      });

      if (!response.ok) {
        throw new Error('Failed to rename material');
      }

      onUploadSuccess();
      handleCancelEditing();
    } catch (error) {
      console.error("Error renaming material:", error);
      handleCancelEditing();
    }
  };

  const handleUploadAndClose = async () => {
    onUploadSuccess();

    await new Promise(resolve => setTimeout(resolve, 1500)); 

    setIsModalOpen(false);
  }

  return (
    <>
      <div className="h-full w-full bg-theme-background rounded-xl flex flex-col relative">
        <div className="h-full flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-theme-border px-6">
            <h2 className="text-lg font-bold text-neutral-text-main">
              參考資料
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            <p className="text-neutral-text-secondary text-sm mb-4">
              {availableSources.length} 個來源
            </p>
            
            <ul className="list-none p-0 m-0 space-y-1 text-gray-700 text-sm">
              {availableSources.map(source => (
                <li key={source.id} className="flex items-center gap-2 p-1 rounded-default hover:bg-theme-background-hover">
                  <input 
                    type="checkbox" 
                    className="form-checkbox h-4 w-4 text-theme-checkbox border-neutral-border rounded focus:ring-theme-ring" 
                    checked={selectedSources.includes(source.id)}
                    onChange={() => onSelectSource(source.id)}
                  />
                  {editingId === source.id ? (
                    <form onSubmit={handleRename} className="flex-1">
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        onBlur={handleCancelEditing}
                        autoFocus
                        className="w-full px-1 py-0 border border-theme-border rounded"
                      />
                    </form>
                  ) : (
                    <>
                      <span className="truncate text-neutral-text-secondary flex-1 cursor-pointer" onClick={() => onSelectSource(source.id)}>
                        {source.name}
                      </span>
                      <button onClick={() => handleStartEditing(source)} className="text-neutral-icon hover:text-theme-primary">
                        <FaEdit />
                      </button>
                    </>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Box 
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
          }}
          onClick={() => setIsModalOpen(true)}
        >
          <Fab color="primary" aria-label="add">
            <AddIcon />
          </Fab>
        </Box>
      </div>

      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        title="新增來源"
      >
        <div>
          <div className="flex border-b mb-4">
            <button 
              onClick={() => setActiveTab('file')}
              className={`py-2 px-4 font-medium ${activeTab === 'file' ? 'border-b-2 border-theme-primary text-theme-primary' : 'text-neutral-text-secondary'}`}
            >
              <span className="flex items-center gap-2"><FaUpload /> 檔案上傳</span>
            </button>
            <button 
              onClick={() => setActiveTab('link')}
              className={`py-2 px-4 font-medium ${activeTab === 'link' ? 'border-b-2 border-theme-primary text-theme-primary' : 'text-neutral-text-secondary'}`}
            >
              <span className="flex items-center gap-2"><FaLink /> 連結</span>
            </button>
          </div>

          <div>
            {activeTab === 'file' && (
              <FileUpload onUploadSuccess={handleUploadAndClose} />
            )}
            {activeTab === 'link' && (
              <div>
                <p className="text-sm text-neutral-text-secondary mb-2">輸入網址來擷取內容。</p>
                <input 
                  type="text"
                  placeholder="https://example.com"
                  className="w-full px-3 py-2 border border-theme-border rounded mb-2"
                />
                <Button 
                  variant="secondary" 
                  className="w-full" 
                  idleText="讀取連結內容"
                />
              </div>
            )}
          </div>
        </div>
      </Modal>
    </>
  );
}

export default SourcePanel;