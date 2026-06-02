/** DocuForge — Custom hook for managing the generation process state. */

import { useCallback, useEffect, useState } from 'react';
import {
  createGenerationStream,
  setImagePlacement,
  startGeneration,
  uploadFiles,
} from '../api/client';
import {
  DEFAULT_SETTINGS,
  type AppSettings,
  type GenerationTask,
  type ImagePlacementRequestBody,
  type UploadedFileInfo,
} from '../types';

export function useDocAgent() {
  // App state
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [detectedImages, setDetectedImages] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Generation state
  const [task, setTask] = useState<GenerationTask | null>(null);
  const [activeEventSource, setActiveEventSource] = useState<EventSource | null>(null);

  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      if (activeEventSource) {
        activeEventSource.close();
      }
    };
  }, [activeEventSource]);

  // File upload handler
  const handleUpload = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setUploadError(null);
    
    try {
      const response = await uploadFiles(files);
      setUploadedFiles((prev) => [...prev, ...response.files]);
      setDetectedImages((prev) => [...prev, ...response.images_detected]);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  }, []);

  // Remove a file
  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.file_id !== fileId));
    setDetectedImages((prev) => prev.filter((f) => f.file_id !== fileId));
  }, []);

  // Start generation
  const generate = useCallback(async () => {
    if (uploadedFiles.length === 0) {
      setUploadError('Please upload at least one file first.');
      return;
    }

    try {
      const fileIds = uploadedFiles.map((f) => f.file_id);
      const response = await startGeneration({
        file_ids: fileIds,
        title: settings.title,
        theme: settings.theme,
        enable_diagrams: settings.enableDiagrams,
        enable_toc: settings.enableToc,
        enable_code_highlighting: settings.enableCodeHighlighting,
        embed_images: settings.embedImages,
        additional_instructions: settings.additionalInstructions,
      });

      // Initialize task state
      setTask({
        taskId: response.task_id,
        status: 'pending',
        progress: 0,
        currentStep: 'Initializing...',
        message: 'Connecting to agent...',
        htmlPreview: null,
        pendingImagePlacements: [],
      });

      // Start SSE stream
      const sse = createGenerationStream(response.task_id);
      setActiveEventSource(sse);

      sse.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.error) {
            setTask((prev) => prev ? { ...prev, status: 'error', message: data.error } : null);
            sse.close();
            return;
          }

          setTask((prev) => {
            if (!prev) return null;
            
            const newTask = {
              ...prev,
              status: data.status,
              progress: data.progress,
              currentStep: data.current_step,
              message: data.message,
            };

            if (data.html_preview) {
              newTask.htmlPreview = data.html_preview;
            }

            if (data.image_placement_required) {
              // Add to pending placements if not already there
              const exists = prev.pendingImagePlacements.some(
                (p) => p.image_id === data.image_placement_required.image_id
              );
              if (!exists) {
                newTask.pendingImagePlacements = [
                  ...prev.pendingImagePlacements,
                  data.image_placement_required,
                ];
              }
            }

            return newTask;
          });

          if (data.status === 'complete' || data.status === 'error') {
            sse.close();
          }
        } catch (err) {
          console.error('Failed to parse SSE message', err);
        }
      };

      sse.onerror = (err) => {
        console.error('SSE Error', err);
        setTask((prev) => prev ? { ...prev, status: 'error', message: 'Connection to agent lost' } : null);
        sse.close();
      };
    } catch (err: any) {
      setUploadError(err.message || 'Failed to start generation');
    }
  }, [uploadedFiles, settings]);

  // Handle image placement decision
  const handleImagePlacement = useCallback(async (request: Omit<ImagePlacementRequestBody, 'task_id'>) => {
    if (!task?.taskId) return;

    try {
      await setImagePlacement({
        task_id: task.taskId,
        ...request,
      });

      // Remove from pending list
      setTask((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          pendingImagePlacements: prev.pendingImagePlacements.filter(
            (p) => p.image_id !== request.image_id
          ),
        };
      });
    } catch (err: any) {
      console.error('Failed to set image placement', err);
      // Depending on requirements, we might want to show this error in the UI
    }
  }, [task?.taskId]);

  return {
    settings,
    setSettings,
    uploadedFiles,
    detectedImages,
    isUploading,
    uploadError,
    handleUpload,
    removeFile,
    generate,
    task,
    handleImagePlacement,
  };
}
