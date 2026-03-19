import { basename, extname, resolve as resolvePath } from 'node:path';
import { readFile, stat } from 'node:fs/promises';

const IMAGE_CAPABILITY_HINTS = new Set([
  'human_detect',
  'image_tagging',
  'face-detect',
  'person-detect',
  'hand-detect',
  'body-keypoints-2d',
  'body-contour-63pt',
  'face-keypoints-106pt',
  'head-pose',
  'face-feature-classification',
  'face-action-classification',
  'face-image-quality',
  'face-emotion-recognition',
  'face-physical-attributes',
  'face-social-attributes',
  'political-figure-recognition',
  'designated-person-recognition',
  'exhibit-image-recognition',
  'person-instance-segmentation',
  'person-semantic-segmentation',
  'concert-cutout',
  'full-body-matting',
  'head-matting',
  'product-cutout'
]);

const MIME_BY_EXTENSION = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.webm': 'audio/webm',
  '.ogg': 'audio/ogg',
  '.m4a': 'audio/mp4',
  '.mp4': 'video/mp4',
  '.mov': 'video/quicktime',
  '.mkv': 'video/webm',
  '.pdf': 'application/pdf',
  '.txt': 'text/plain',
  '.md': 'text/markdown',
  '.markdown': 'text/markdown'
};

const MAX_UPLOAD_BYTES_BY_KIND = {
  image: 25 * 1024 * 1024,
  audio: 25 * 1024 * 1024,
  video: 100 * 1024 * 1024,
  file: 25 * 1024 * 1024
};

export async function resolvePublicUploadCandidate(payloadRaw) {
  const payload = toObject(payloadRaw);
  const input = toObject(payload.input);
  const attachment = mergeObjects(toObject(payload.attachment), toObject(input.attachment));
  const capability = readText(payload.capability);

  if (hasDirectMediaUrl(payload, input, attachment)) {
    return null;
  }

  const filePath = readText(input.file_path) || readText(payload.file_path) || readAttachmentPath(attachment);
  if (filePath) {
    const fileName = resolveFileName(attachment, filePath);
    const contentType = resolveContentType(attachment, filePath, fileName, capability);
    const targetField = inferTargetField(capability, contentType, fileName);
    await assertReadableAttachmentPath(filePath, contentType, targetField);
    return {
      sourceKind: 'file_path',
      filePath,
      fileName,
      contentType,
      targetField
    };
  }

  const rawBytesSource = readAttachmentBytesSource(attachment) ?? readAttachmentBytesSource(input.attachment);
  if (rawBytesSource === null) {
    return null;
  }

  const bytes = decodeBytes(rawBytesSource);
  if (bytes.length === 0) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'attachment bytes are empty', {
      bridge_step: 'prepare_upload'
    });
  }

  const fileName = resolveFileName(attachment, null);
  const contentType = resolveContentType(attachment, null, fileName, capability);
  const targetField = inferTargetField(capability, contentType, fileName);

  return {
    sourceKind: 'attachment_bytes',
    bytes,
    fileName,
    contentType,
    targetField
  };
}

export async function uploadCandidateThroughPublicBridge(candidate, auth, fetchImpl) {
  if (!candidate) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'upload candidate is required', {
      bridge_step: 'prepare_upload'
    });
  }

  const fileBuffer =
    candidate.sourceKind === 'file_path'
      ? await readFile(candidate.filePath)
      : candidate.bytes;
  const contentType = candidate.contentType ?? resolveFallbackContentType(candidate.targetField);

  if (!Buffer.isBuffer(fileBuffer) || fileBuffer.length === 0) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'file body is required', {
      bridge_step: 'prepare_upload'
    });
  }

  const form = new FormData();
  form.set('entry_host', auth.entryHost);
  form.set('agent_uid', auth.agentUid);
  form.set('conversation_id', auth.conversationId);
  if (readText(auth.entryUserKey)) {
    form.set('entry_user_key', auth.entryUserKey);
  }
  form.set('file_name', candidate.fileName);
  form.set('content_type', contentType);
  form.set('file', new Blob([fileBuffer], { type: contentType }), candidate.fileName);

  const response = await fetchImpl(`${auth.baseUrl}/agent/public-bridge/upload-file`, {
    method: 'POST',
    body: form
  });
  const text = await response.text();
  const parsed = parseJson(text);

  if (!response.ok || (parsed && typeof parsed === 'object' && parsed.error)) {
    const apiError = parseApiError(parsed, text, response.status);
    throw createUploadError(apiError.status, apiError.code, apiError.message, apiError.details);
  }

  const data = parsed && typeof parsed === 'object' ? parsed.data : null;
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw createUploadError(502, 'UPSTREAM_UNAVAILABLE', 'invalid upload response');
  }

  const url = typeof data.url === 'string' ? data.url.trim() : '';
  if (!url) {
    throw createUploadError(502, 'UPSTREAM_UNAVAILABLE', 'upload response missing url');
  }

  return {
    url,
    pathname: typeof data.pathname === 'string' ? data.pathname : '',
    content_type: typeof data.content_type === 'string' ? data.content_type : contentType,
    upload_kind: typeof data.upload_kind === 'string' ? data.upload_kind : inferUploadKind(contentType, candidate.targetField)
  };
}

export function applyUploadedAttachment(payloadRaw, candidate, uploaded) {
  const payload = toObject(payloadRaw);
  const next = {
    ...payload,
    input: sanitizeUploadSources({
      ...toObject(payload.input),
      [candidate.targetField]: uploaded.url
    })
  };

  return sanitizeUploadSources(next);
}

function hasDirectMediaUrl(payload, input, attachment) {
  return readText(input.image_url) !== null ||
    readText(payload.image_url) !== null ||
    readText(input.audio_url) !== null ||
    readText(payload.audio_url) !== null ||
    readText(input.file_url) !== null ||
    readText(payload.file_url) !== null ||
    readText(input.video_url) !== null ||
    readText(payload.video_url) !== null ||
    readText(attachment.url) !== null;
}

function resolveFileName(attachment, filePath) {
  const candidate =
    readText(attachment.file_name) ||
    readText(attachment.filename) ||
    readText(attachment.name) ||
    readText(attachment.fileName) ||
    (filePath ? basename(filePath) : '');
  return candidate || 'upload.bin';
}

function resolveContentType(attachment, filePath, fileName, capability) {
  const direct =
    readText(attachment.content_type) ||
    readText(attachment.mime_type) ||
    readText(attachment.mimeType) ||
    readText(attachment.type) ||
    readText(attachment.contentType);
  if (direct) {
    return normalizeContentType(direct) ?? direct;
  }

  const inferred = normalizeContentType(MIME_BY_EXTENSION[extname(fileName || filePath || '').toLowerCase()] ?? '');
  if (inferred) {
    return inferred;
  }

  if (capability === 'asr' || /audio/i.test(capability)) {
    return 'audio/mpeg';
  }
  if (capability === 'markdown_convert' || /document|file|markdown/i.test(capability)) {
    return 'text/markdown';
  }
  if (capability === 'tencent-video-face-fusion' || /video/i.test(capability)) {
    return 'video/mp4';
  }
  if (IMAGE_CAPABILITY_HINTS.has(capability) || /image|detect|tag|pose|segment|matting|recognition|classification|quality/i.test(capability)) {
    return 'image/png';
  }

  return null;
}

function inferTargetField(capability, contentType, fileName) {
  const mediaKind = inferMediaKind(contentType, fileName);
  if (mediaKind === 'image') {
    return 'image_url';
  }
  if (mediaKind === 'audio') {
    return 'audio_url';
  }
  if (mediaKind === 'video') {
    return 'video_url';
  }
  if (mediaKind === 'file') {
    return 'file_url';
  }

  if (capability === 'asr' || /audio/i.test(capability)) {
    return 'audio_url';
  }
  if (capability === 'markdown_convert' || /document|file|markdown/i.test(capability)) {
    return 'file_url';
  }
  if (capability === 'tencent-video-face-fusion' || /video/i.test(capability)) {
    return 'video_url';
  }
  return 'image_url';
}

function inferMediaKind(contentType, fileName) {
  const mime = normalizeContentType(contentType) ?? '';
  const ext = extname(fileName || '').toLowerCase();
  const extMime = MIME_BY_EXTENSION[ext] ?? '';
  const resolved = mime || extMime;

  if (resolved.startsWith('image/')) {
    return 'image';
  }
  if (resolved.startsWith('audio/')) {
    return 'audio';
  }
  if (resolved.startsWith('video/')) {
    return 'video';
  }
  if (resolved === 'application/pdf' || resolved === 'text/plain' || resolved === 'text/markdown') {
    return 'file';
  }
  return null;
}

function inferUploadKind(contentType, targetField) {
  const kind = inferMediaKind(contentType, '');
  if (kind) {
    return kind;
  }
  if (targetField === 'audio_url') {
    return 'audio';
  }
  if (targetField === 'video_url') {
    return 'video';
  }
  if (targetField === 'file_url') {
    return 'file';
  }
  return 'image';
}

function resolveFallbackContentType(targetField) {
  if (targetField === 'audio_url') {
    return 'audio/mpeg';
  }
  if (targetField === 'video_url') {
    return 'video/mp4';
  }
  if (targetField === 'file_url') {
    return 'application/octet-stream';
  }
  return 'image/png';
}

function readAttachmentPath(attachment) {
  return readText(attachment.path) || readText(attachment.file_path) || readText(attachment.filePath);
}

function readAttachmentBytesSource(attachment) {
  return attachment.bytes ?? attachment.base64 ?? attachment.data ?? attachment.content ?? attachment.buffer ?? null;
}

function decodeBytes(value) {
  if (Buffer.isBuffer(value)) {
    return value;
  }
  if (value instanceof Uint8Array) {
    return Buffer.from(value);
  }
  if (ArrayBuffer.isView(value)) {
    return Buffer.from(value.buffer, value.byteOffset, value.byteLength);
  }
  if (value instanceof ArrayBuffer) {
    return Buffer.from(value);
  }
  if (value && typeof value === 'object' && value.type === 'Buffer' && Array.isArray(value.data)) {
    return Buffer.from(value.data);
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) {
      return Buffer.alloc(0);
    }
    if (trimmed.startsWith('data:')) {
      const commaIndex = trimmed.indexOf(',');
      if (commaIndex === -1) {
        return Buffer.alloc(0);
      }
      const meta = trimmed.slice(5, commaIndex);
      const data = trimmed.slice(commaIndex + 1);
      if (meta.includes(';base64')) {
        return Buffer.from(data, 'base64');
      }
      return Buffer.from(decodeURIComponent(data), 'utf8');
    }
    if (looksLikeBase64(trimmed)) {
      return Buffer.from(trimmed, 'base64');
    }
    return Buffer.from(trimmed, 'utf8');
  }

  return Buffer.alloc(0);
}

async function assertReadableAttachmentPath(filePath, contentType, targetField) {
  assertNoParentTraversal(filePath);
  const resolvedPath = resolvePath(filePath);
  const normalized = resolvedPath.replace(/\\/g, '/').toLowerCase();
  const blockedSegments = ['/.ssh', '/.aws', '/.config', '/.git', '/etc'];

  if (blockedSegments.some((segment) => normalized === segment || normalized.includes(`${segment}/`))) {
    throw createUploadError(
      400,
      'VALIDATION_BAD_REQUEST',
      'attachment file_path points to a restricted local path',
      { bridge_step: 'prepare_upload' }
    );
  }

  let fileStat;
  try {
    fileStat = await stat(resolvedPath);
  } catch {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'attachment file_path does not exist', {
      bridge_step: 'prepare_upload'
    });
  }

  if (!fileStat.isFile()) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'attachment file_path must point to a file', {
      bridge_step: 'prepare_upload'
    });
  }

  const uploadKind = inferUploadKind(contentType, targetField);
  const maxBytes = MAX_UPLOAD_BYTES_BY_KIND[uploadKind] ?? MAX_UPLOAD_BYTES_BY_KIND.image;
  if (fileStat.size > maxBytes) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', `${uploadKind} file exceeds local upload limit`, {
      bridge_step: 'prepare_upload',
      max_bytes: maxBytes
    });
  }

  if (!normalizeContentType(contentType) || inferMediaKind(contentType, basename(resolvedPath)) === null) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'attachment file_path content type is not allowed', {
      bridge_step: 'prepare_upload'
    });
  }
}

function assertNoParentTraversal(filePath) {
  const normalized = filePath.replace(/\\/g, '/');
  const segments = normalized.split('/');
  if (segments.includes('..')) {
    throw createUploadError(400, 'VALIDATION_BAD_REQUEST', 'attachment file_path must not contain parent traversal', {
      bridge_step: 'prepare_upload'
    });
  }
}

function looksLikeBase64(value) {
  if (value.length < 8 || value.length % 4 !== 0) {
    return false;
  }
  return /^[A-Za-z0-9+/=\r\n]+$/.test(value);
}

function normalizeContentType(value) {
  const text = readText(value);
  if (!text) {
    return null;
  }
  const [contentType] = text.split(';');
  return readText(contentType)?.toLowerCase() ?? null;
}

function readText(value) {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function sanitizeUploadSources(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return value;
  }

  const next = { ...value };
  delete next.file_path;
  delete next.filePath;
  delete next.bytes;
  delete next.base64;
  delete next.data;
  delete next.content;
  delete next.buffer;

  if (next.attachment && typeof next.attachment === 'object' && !Array.isArray(next.attachment)) {
    const attachment = { ...next.attachment };
    delete attachment.path;
    delete attachment.file_path;
    delete attachment.filePath;
    delete attachment.bytes;
    delete attachment.base64;
    delete attachment.data;
    delete attachment.content;
    delete attachment.buffer;
    next.attachment = attachment;
  }

  return next;
}

function toObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {};
  }
  return { ...value };
}

function mergeObjects(primary, secondary) {
  return {
    ...secondary,
    ...primary
  };
}

function parseJson(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function parseApiError(parsed, fallbackMessage, status) {
  const error = parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed.error : null;
  if (error && typeof error === 'object' && !Array.isArray(error)) {
    return {
      status: Number.isFinite(error.status) ? error.status : status,
      code: typeof error.code === 'string' ? error.code : 'SYSTEM_INTERNAL_ERROR',
      message: typeof error.message === 'string' ? error.message : fallbackMessage,
      details: error.details
    };
  }

  return {
    status,
    code: 'SYSTEM_INTERNAL_ERROR',
    message: fallbackMessage,
    details: undefined
  };
}

function createUploadError(status, code, message, details = undefined) {
  const error = new Error(message);
  error.status = status;
  error.code = code;
  error.details = details;
  return error;
}
