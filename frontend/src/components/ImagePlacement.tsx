import { useState } from 'react';
import type { ImagePlacement, ImagePlacementInfo, ImagePlacementRequestBody } from '../types';

interface ImagePlacementProps {
  placementRequests: ImagePlacementInfo[];
  onSubmit: (request: Omit<ImagePlacementRequestBody, 'task_id'>) => void;
}

export function ImagePlacementModal({ placementRequests, onSubmit }: ImagePlacementProps) {
  const [selectedPlacement, setSelectedPlacement] = useState<ImagePlacement>('after_section');
  
  if (placementRequests.length === 0) return null;

  const currentRequest = placementRequests[0]; // Handle one at a time

  const handleSubmit = () => {
    onSubmit({
      image_id: currentRequest.image_id,
      placement: selectedPlacement,
      section_id: null, // Basic implementation - would need section selector for production
    });
    setSelectedPlacement('after_section');
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem', color: 'var(--text-primary)' }}>
          Image Placement Needed
        </h2>
        
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          The agent detected an image during generation. Where should it be placed in the document?
        </p>

        <div style={{ 
          marginBottom: '2rem', 
          padding: '1rem', 
          backgroundColor: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-md)',
          textAlign: 'center' 
        }}>
          <img 
            src={currentRequest.preview_url} 
            alt={currentRequest.filename} 
            style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: 'var(--radius-sm)', objectFit: 'contain' }}
          />
          <p style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            {currentRequest.filename}
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 500, color: 'var(--text-primary)' }}>
            Select Placement:
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="placement" 
                value="hero_banner" 
                checked={selectedPlacement === 'hero_banner'}
                onChange={(e) => setSelectedPlacement(e.target.value as ImagePlacement)}
              />
              <span style={{ color: 'var(--text-primary)' }}>Hero Banner (Top of document)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="placement" 
                value="after_section" 
                checked={selectedPlacement === 'after_section'}
                onChange={(e) => setSelectedPlacement(e.target.value as ImagePlacement)}
              />
              <span style={{ color: 'var(--text-primary)' }}>Auto (Let agent decide)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="placement" 
                value="appendix" 
                checked={selectedPlacement === 'appendix'}
                onChange={(e) => setSelectedPlacement(e.target.value as ImagePlacement)}
              />
              <span style={{ color: 'var(--text-primary)' }}>Appendix (Bottom of document)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="placement" 
                value="skip" 
                checked={selectedPlacement === 'skip'}
                onChange={(e) => setSelectedPlacement(e.target.value as ImagePlacement)}
              />
              <span style={{ color: 'var(--text-muted)' }}>Skip (Do not include)</span>
            </label>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button 
            className="btn btn-primary" 
            onClick={handleSubmit}
          >
            Confirm Placement
          </button>
        </div>
      </div>
    </div>
  );
}
