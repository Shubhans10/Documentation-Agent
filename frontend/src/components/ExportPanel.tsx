import { getExportUrl } from '../api/client';
import type { GenerationTask } from '../types';

interface ExportPanelProps {
  task: GenerationTask | null;
}

export function ExportPanel({ task }: ExportPanelProps) {
  const isComplete = task?.status === 'complete';
  const hasError = task?.status === 'error';

  return (
    <div className="glass-card" style={{ padding: '1.5rem' }}>
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', color: 'var(--text-secondary)' }}>Export</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ padding: '1rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Status</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '10px', 
              height: '10px', 
              borderRadius: '50%', 
              backgroundColor: isComplete ? 'var(--success)' : hasError ? 'var(--error)' : task ? 'var(--warning)' : 'var(--text-muted)',
              boxShadow: isComplete ? '0 0 8px rgba(34, 197, 94, 0.4)' : hasError ? '0 0 8px rgba(239, 68, 68, 0.4)' : task ? '0 0 8px rgba(245, 158, 11, 0.4)' : 'none'
            }}></div>
            <span style={{ fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
              {task?.status || 'Waiting'}
            </span>
          </div>
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.875rem' }}
          disabled={!isComplete || !task?.taskId}
          onClick={() => {
            if (task?.taskId) {
              window.open(getExportUrl(task.taskId), '_blank');
            }
          }}
        >
          <span style={{ marginRight: '0.5rem' }}>⬇️</span> Download HTML
        </button>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
          Self-contained HTML file with embedded styles and images.
        </p>
      </div>
    </div>
  );
}
