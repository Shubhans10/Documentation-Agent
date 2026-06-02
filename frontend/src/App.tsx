import { useDocAgent } from './hooks/useDocAgent';
import { FileUpload } from './components/FileUpload';
import { SettingsPanel } from './components/SettingsPanel';
import { LivePreview } from './components/LivePreview';
import { ChatInterface } from './components/ChatInterface';
import { ExportPanel } from './components/ExportPanel';
import { ImagePlacementModal } from './components/ImagePlacement';
import './index.css';

function App() {
  const {
    settings,
    setSettings,
    uploadedFiles,
    isUploading,
    uploadError,
    handleUpload,
    removeFile,
    generate,
    task,
    handleImagePlacement,
  } = useDocAgent();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      
      {/* Header */}
      <header style={{ 
        padding: '1rem 2rem', 
        backgroundColor: 'var(--bg-secondary)', 
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '10px', 
            background: 'linear-gradient(135deg, var(--accent), var(--violet))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '1.2rem',
            boxShadow: '0 4px 12px var(--accent-glow)'
          }}>
            DF
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', margin: 0, background: 'linear-gradient(90deg, #fff, #a5b4fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              DocuForge
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>AI Documentation Agent</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, display: 'flex', overflow: 'hidden', padding: '1.5rem', gap: '1.5rem' }}>
        
        {/* Left Sidebar: Upload & Settings */}
        <div style={{ width: '340px', display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '0.5rem' }}>
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <FileUpload
              uploadedFiles={uploadedFiles}
              isUploading={isUploading}
              uploadError={uploadError}
              onUpload={handleUpload}
              onRemove={removeFile}
            />
            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.5rem 0' }} />
            <SettingsPanel
              settings={settings}
              onChange={setSettings}
              onGenerate={generate}
              isGenerating={task?.status === 'pending' || task?.status === 'processing'}
              canGenerate={uploadedFiles.length > 0}
            />
          </div>
        </div>

        {/* Center: Live Preview */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <LivePreview task={task} />
        </div>

        {/* Right Sidebar: Chat & Export */}
        <div style={{ width: '340px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <ExportPanel task={task} />
          <div style={{ flex: 1, minHeight: 0 }}>
             <ChatInterface task={task} />
          </div>
        </div>

      </main>

      {/* Modals */}
      {task?.pendingImagePlacements && task.pendingImagePlacements.length > 0 && (
        <ImagePlacementModal 
          placementRequests={task.pendingImagePlacements} 
          onSubmit={handleImagePlacement} 
        />
      )}
    </div>
  );
}

export default App;
