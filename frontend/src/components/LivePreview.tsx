import { useEffect, useRef } from 'react';
import type { GenerationTask } from '../types';

interface LivePreviewProps {
  task: GenerationTask | null;
}

export function LivePreview({ task }: LivePreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Update iframe content when htmlPreview changes
  useEffect(() => {
    if (iframeRef.current && task?.htmlPreview) {
      const doc = iframeRef.current.contentDocument;
      if (doc) {
        doc.open();
        doc.write(task.htmlPreview);
        doc.close();
      }
    }
  }, [task?.htmlPreview]);

  if (!task) {
    return (
      <div 
        className="glass-card" 
        style={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'var(--text-muted)'
        }}
      >
        <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📝</div>
        <p>Upload files and click Generate to see the preview.</p>
      </div>
    );
  }

  const isGenerating = task.status === 'pending' || task.status === 'processing' || task.status === 'awaiting_input';
  
  return (
    <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ 
        padding: '1rem 1.5rem', 
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'var(--bg-tertiary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h3 style={{ fontSize: '1rem', margin: 0 }}>Preview</h3>
          {isGenerating && (
            <span className="badge badge-accent animate-pulse">Generating</span>
          )}
          {task.status === 'complete' && (
            <span className="badge badge-success">Complete</span>
          )}
          {task.status === 'error' && (
            <span className="badge badge-error">Error</span>
          )}
        </div>
        
        {isGenerating && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            <span>{task.currentStep}</span>
            <div style={{ width: '100px' }}>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${task.progress * 100}%` }}></div>
              </div>
            </div>
            <span>{Math.round(task.progress * 100)}%</span>
          </div>
        )}
      </div>

      {/* Iframe Container */}
      <div style={{ flex: 1, backgroundColor: '#fff', position: 'relative' }}>
        {task.htmlPreview ? (
          <iframe
            ref={iframeRef}
            title="Documentation Preview"
            style={{ width: '100%', height: '100%', border: 'none' }}
            sandbox="allow-same-origin allow-scripts"
          />
        ) : (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem' }}>
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-muted)' }}>{task.message || 'Initializing agent...'}</p>
          </div>
        )}
      </div>
    </div>
  );
}
