/** DocuForge — TypeScript type definitions */

// ---------------------------------------------------------------------------
// File Types
// ---------------------------------------------------------------------------

export type FileType = 'text' | 'pdf' | 'markdown' | 'image';

export type Theme = 'modern_dark' | 'clean_light' | 'technical_blueprint';

export type ImagePlacement = 'hero_banner' | 'after_section' | 'appendix' | 'inline' | 'skip';

export type GenerationStatus = 'pending' | 'processing' | 'awaiting_input' | 'complete' | 'error';

// ---------------------------------------------------------------------------
// File Upload
// ---------------------------------------------------------------------------

export interface UploadedFileInfo {
  file_id: string;
  filename: string;
  file_type: FileType;
  size_bytes: number;
  is_image: boolean;
  preview_url: string | null;
}

export interface UploadResponse {
  files: UploadedFileInfo[];
  images_detected: UploadedFileInfo[];
  message: string;
}

// ---------------------------------------------------------------------------
// Generation
// ---------------------------------------------------------------------------

export interface GenerateRequest {
  file_ids: string[];
  title: string;
  theme: Theme;
  enable_diagrams: boolean;
  enable_toc: boolean;
  enable_code_highlighting: boolean;
  embed_images: boolean;
  additional_instructions: string;
}

export interface GenerateProgress {
  task_id: string;
  status: GenerationStatus;
  progress: number;
  current_step: string;
  message: string;
  html_preview: string | null;
  image_placement_required: ImagePlacementInfo | null;
}

export interface ImagePlacementInfo {
  image_id: string;
  filename: string;
  preview_url: string;
  available_sections: string[];
}

export interface ImagePlacementRequestBody {
  task_id: string;
  image_id: string;
  placement: ImagePlacement;
  section_id: string | null;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export interface ChatMessage {
  task_id: string;
  message: string;
}

export interface ChatResponse {
  message: string;
  updated_preview: boolean;
}

// ---------------------------------------------------------------------------
// App Settings (local state)
// ---------------------------------------------------------------------------

export interface AppSettings {
  title: string;
  theme: Theme;
  enableDiagrams: boolean;
  enableToc: boolean;
  enableCodeHighlighting: boolean;
  embedImages: boolean;
  additionalInstructions: string;
}

export const DEFAULT_SETTINGS: AppSettings = {
  title: 'Documentation',
  theme: 'modern_dark',
  enableDiagrams: true,
  enableToc: true,
  enableCodeHighlighting: true,
  embedImages: true,
  additionalInstructions: '',
};

// ---------------------------------------------------------------------------
// Generation Task (combined state)
// ---------------------------------------------------------------------------

export interface GenerationTask {
  taskId: string;
  status: GenerationStatus;
  progress: number;
  currentStep: string;
  message: string;
  htmlPreview: string | null;
  pendingImagePlacements: ImagePlacementInfo[];
}
