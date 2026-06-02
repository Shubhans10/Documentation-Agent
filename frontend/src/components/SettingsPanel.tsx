import type { AppSettings, Theme } from '../types';

interface SettingsPanelProps {
  settings: AppSettings;
  onChange: (settings: AppSettings) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  canGenerate: boolean;
}

export function SettingsPanel({
  settings,
  onChange,
  onGenerate,
  isGenerating,
  canGenerate,
}: SettingsPanelProps) {
  
  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    onChange({ ...settings, [key]: value });
  };

  return (
    <div className="settings-panel">
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', color: 'var(--text-secondary)' }}>Settings</h3>
      
      {/* Title */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Document Title
        </label>
        <input
          type="text"
          className="input"
          value={settings.title}
          onChange={(e) => updateSetting('title', e.target.value)}
          placeholder="e.g. API Reference"
          disabled={isGenerating}
        />
      </div>

      {/* Theme */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Theme
        </label>
        <select
          className="select"
          value={settings.theme}
          onChange={(e) => updateSetting('theme', e.target.value as Theme)}
          disabled={isGenerating}
        >
          <option value="modern_dark">Modern Dark</option>
          <option value="clean_light">Clean Light</option>
          <option value="technical_blueprint">Technical Blueprint</option>
        </select>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.5rem 0' }} />

      {/* Toggles */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        
        {/* Diagrams */}
        <label className="toggle-wrapper" style={{ cursor: isGenerating ? 'not-allowed' : 'pointer', opacity: isGenerating ? 0.6 : 1 }}>
          <div className="toggle-label">
            <span className="toggle-label-text">Generate Diagrams</span>
            <span className="toggle-label-hint">Create Mermaid.js charts</span>
          </div>
          <div className="toggle">
            <input
              type="checkbox"
              checked={settings.enableDiagrams}
              onChange={(e) => updateSetting('enableDiagrams', e.target.checked)}
              disabled={isGenerating}
            />
            <div className="toggle-track"></div>
          </div>
        </label>

        {/* TOC */}
        <label className="toggle-wrapper" style={{ cursor: isGenerating ? 'not-allowed' : 'pointer', opacity: isGenerating ? 0.6 : 1 }}>
          <div className="toggle-label">
            <span className="toggle-label-text">Table of Contents</span>
            <span className="toggle-label-hint">Auto-generate from headings</span>
          </div>
          <div className="toggle">
            <input
              type="checkbox"
              checked={settings.enableToc}
              onChange={(e) => updateSetting('enableToc', e.target.checked)}
              disabled={isGenerating}
            />
            <div className="toggle-track"></div>
          </div>
        </label>

        {/* Code Highlighting */}
        <label className="toggle-wrapper" style={{ cursor: isGenerating ? 'not-allowed' : 'pointer', opacity: isGenerating ? 0.6 : 1 }}>
          <div className="toggle-label">
            <span className="toggle-label-text">Code Highlighting</span>
            <span className="toggle-label-hint">Syntax colors via Prism.js</span>
          </div>
          <div className="toggle">
            <input
              type="checkbox"
              checked={settings.enableCodeHighlighting}
              onChange={(e) => updateSetting('enableCodeHighlighting', e.target.checked)}
              disabled={isGenerating}
            />
            <div className="toggle-track"></div>
          </div>
        </label>
        
      </div>

      <div style={{ marginTop: '2.5rem' }}>
        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.875rem' }}
          onClick={onGenerate}
          disabled={!canGenerate || isGenerating}
        >
          {isGenerating ? (
            <>
              <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
              Generating...
            </>
          ) : (
            'Generate Documentation'
          )}
        </button>
      </div>
    </div>
  );
}
