import { useCallback, useRef, useState } from 'react';
import type { UploadedFileInfo } from '../types';

interface FileUploadProps {
  uploadedFiles: UploadedFileInfo[];
  isUploading: boolean;
  uploadError: string | null;
  onUpload: (files: File[]) => void;
  onRemove: (fileId: string) => void;
}

export function FileUpload({
  uploadedFiles,
  isUploading,
  uploadError,
  onUpload,
  onRemove,
}: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(Array.from(e.target.files));
    }
    // Reset input so the same file can be selected again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(Array.from(e.dataTransfer.files));
    }
  }, [onUpload]);

  return (
    <div className="upload-container" style={{ marginBottom: '2rem' }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: 'var(--text-secondary)' }}>Source Files</h3>
      
      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '2rem',
          textAlign: 'center',
          backgroundColor: isDragging ? 'var(--accent-glow)' : 'var(--bg-input)',
          transition: 'all var(--transition-normal)',
          cursor: 'pointer',
        }}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
          multiple
          accept=".txt,.pdf,.md,.markdown,.png,.jpg,.jpeg,.gif,.webp,.svg"
        />
        
        {isUploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <div className="spinner"></div>
            <p style={{ color: 'var(--accent-light)' }}>Uploading files...</p>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📄</div>
            <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Click or drag files here</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              TXT, PDF, MD, and Images
            </p>
          </div>
        )}
      </div>

      {uploadError && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-sm)', color: 'var(--error)', fontSize: '0.875rem' }}>
          {uploadError}
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Uploaded</h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {uploadedFiles.map((file) => (
              <li 
                key={file.file_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', overflow: 'hidden' }}>
                  <span style={{ fontSize: '1.2rem' }}>
                    {file.is_image ? '🖼️' : file.file_type === 'pdf' ? '📕' : '📝'}
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {file.filename}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {(file.size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
                <button
                  className="btn-ghost btn-icon"
                  style={{ color: 'var(--text-muted)' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(file.file_id);
                  }}
                  title="Remove file"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
