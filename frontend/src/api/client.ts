/** DocuForge — API client for communicating with the FastAPI backend. */

import type {
  ChatMessage,
  ChatResponse,
  GenerateRequest,
  ImagePlacementRequestBody,
  UploadResponse,
} from '../types';

const API_BASE = 'http://localhost:8000/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function checkHealth(): Promise<{ status: string; api_key_configured: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse(res);
}

// ---------------------------------------------------------------------------
// File Upload
// ---------------------------------------------------------------------------

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}

// ---------------------------------------------------------------------------
// Generation
// ---------------------------------------------------------------------------

export async function startGeneration(
  request: GenerateRequest
): Promise<{ task_id: string; stream_url: string }> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse(res);
}

export function createGenerationStream(taskId: string): EventSource {
  return new EventSource(`${API_BASE}/generate/${taskId}/stream`);
}

// ---------------------------------------------------------------------------
// Image Placement
// ---------------------------------------------------------------------------

export async function setImagePlacement(request: ImagePlacementRequestBody): Promise<void> {
  const res = await fetch(`${API_BASE}/image-placement`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Preview & Export
// ---------------------------------------------------------------------------

export async function getPreview(taskId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/preview/${taskId}`);
  if (!res.ok) throw new Error('Preview not available');
  return res.text();
}

export function getExportUrl(taskId: string): string {
  return `${API_BASE}/export/${taskId}`;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export async function sendChatMessage(message: ChatMessage): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(message),
  });
  return handleResponse<ChatResponse>(res);
}
