#!/usr/bin/env node

import { basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { AGENT_TASK_DEFAULT_BASE_URL, resolveAgentTaskAuth } from './agent-task-auth.mjs';
import { normalizeExecutePayload } from './attachment-normalize.mjs';
import {
  applyUploadedAttachment,
  resolvePublicUploadCandidate,
  uploadCandidateThroughPublicBridge
} from './public-upload.mjs';
import { emitTelemetry, extractRequestContext } from './telemetry.mjs';

const ACTIONS = {
  'portal.skill.execute': { method: 'POST' },
  'portal.skill.poll': { method: 'GET' },
  'portal.skill.presentation': { method: 'GET' },
  'portal.account.balance': { method: 'GET' },
  'portal.account.ledger': { method: 'GET' }
};

const IMAGE_CAPABILITIES = new Set([
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
const NON_VISUAL_SERVICE_IDS = new Set([
  'svc_cf_tts_report',
  'svc_cf_embeddings',
  'svc_cf_reranker',
  'svc_cf_asr',
  'svc_cf_tts_low_cost',
  'svc_cf_markdown_convert'
]);
const GUIDANCE_ASSET_PRIORITY = ['overlay', 'cutout', 'mask'];
const CAPABILITY_SERVICE_MAP = {
  human_detect: 'svc_cf_human_detect',
  image_tagging: 'svc_cf_image_tagging',
  tts_report: 'svc_cf_tts_report',
  embeddings: 'svc_cf_embeddings',
  reranker: 'svc_cf_reranker',
  asr: 'svc_cf_asr',
  tts_low_cost: 'svc_cf_tts_low_cost',
  markdown_convert: 'svc_cf_markdown_convert',
  'face-detect': 'svc_cv_face_detect',
  'person-detect': 'svc_cv_person_detect',
  'hand-detect': 'svc_cv_hand_detect',
  'body-keypoints-2d': 'svc_cv_body_keypoints_2d',
  'body-contour-63pt': 'svc_cv_body_contour_63pt',
  'face-keypoints-106pt': 'svc_cv_face_keypoints_106pt',
  'head-pose': 'svc_cv_head_pose',
  'face-feature-classification': 'svc_cv_face_feature_classification',
  'face-action-classification': 'svc_cv_face_action_classification',
  'face-image-quality': 'svc_cv_face_image_quality',
  'face-emotion-recognition': 'svc_cv_face_emotion_recognition',
  'face-physical-attributes': 'svc_cv_face_physical_attributes',
  'face-social-attributes': 'svc_cv_face_social_attributes',
  'political-figure-recognition': 'svc_cv_political_figure_recognition',
  'designated-person-recognition': 'svc_cv_designated_person_recognition',
  'exhibit-image-recognition': 'svc_cv_exhibit_image_recognition',
  'person-instance-segmentation': 'svc_cv_person_instance_segmentation',
  'person-semantic-segmentation': 'svc_cv_person_semantic_segmentation',
  'concert-cutout': 'svc_cv_concert_cutout',
  'full-body-matting': 'svc_cv_full_body_matting',
  'head-matting': 'svc_cv_head_matting',
  'product-cutout': 'svc_cv_product_cutout'
};
const SERVICE_CAPABILITY_HINTS = Object.fromEntries(
  Object.entries(CAPABILITY_SERVICE_MAP).map(([capability, serviceId]) => [serviceId, capability])
);
const VISUAL_PLAYBOOK_PRESETS = {
  detection: {
    display_mode: 'bbox_overlay',
    preferred_assets: ['overlay', 'source'],
    summary_fields: ['object_count', 'top_confidence', 'bbox_xyxy'],
    chat_template: 'detection_summary_with_boxes'
  },
  classification: {
    display_mode: 'topk_labels',
    preferred_assets: ['source'],
    summary_fields: ['top_labels', 'top_label_score'],
    chat_template: 'classification_topk_summary'
  },
  keypoints: {
    display_mode: 'pose_keypoints_overlay',
    preferred_assets: ['overlay', 'source'],
    summary_fields: ['keypoint_count', 'body_bbox'],
    quality_checks: ['point_outlier_check'],
    chat_template: 'keypoint_summary_with_anomaly_hint'
  },
  segmentation: {
    display_mode: 'instance_mask_overlay',
    preferred_assets: ['overlay', 'mask', 'source'],
    summary_fields: ['instance_count', 'mask_presence'],
    chat_template: 'segmentation_summary_with_overlay'
  },
  matting: {
    display_mode: 'matting_triptych',
    preferred_assets: ['cutout', 'mask', 'overlay'],
    summary_fields: ['cutout_ready', 'mask_ready'],
    chat_template: 'matting_delivery_summary'
  }
};
const VISUAL_PLAYBOOK_PRESET_BY_CAPABILITY = {
  human_detect: 'detection',
  'face-detect': 'detection',
  'person-detect': 'detection',
  'hand-detect': 'detection',
  image_tagging: 'classification',
  'face-feature-classification': 'classification',
  'face-action-classification': 'classification',
  'face-image-quality': 'classification',
  'face-emotion-recognition': 'classification',
  'face-physical-attributes': 'classification',
  'face-social-attributes': 'classification',
  'political-figure-recognition': 'classification',
  'designated-person-recognition': 'classification',
  'exhibit-image-recognition': 'classification',
  'body-keypoints-2d': 'keypoints',
  'body-contour-63pt': 'keypoints',
  'face-keypoints-106pt': 'keypoints',
  'head-pose': 'keypoints',
  'person-instance-segmentation': 'segmentation',
  'person-semantic-segmentation': 'segmentation',
  'concert-cutout': 'segmentation',
  'product-cutout': 'segmentation',
  'full-body-matting': 'matting',
  'head-matting': 'matting'
};
const VISUAL_PLAYBOOK_OVERRIDES = {
  'body-contour-63pt': {
    display_mode: 'contour_points_overlay',
    summary_fields: ['landmark_count', 'availability_status'],
    fallback_capability: 'body-keypoints-2d',
    chat_template: 'contour_summary_with_fallback'
  },
  'face-keypoints-106pt': {
    summary_fields: ['landmark_count', 'face_bbox']
  },
  'head-pose': {
    summary_fields: ['head_pose_points', 'face_bbox']
  },
  'person-semantic-segmentation': {
    display_mode: 'semantic_mask_overlay',
    summary_fields: ['semantic_mask_presence', 'class_map_presence']
  },
  'full-body-matting': {
    display_mode: 'full_body_matting_triptych'
  },
  'head-matting': {
    display_mode: 'head_matting_triptych'
  },
  'product-cutout': {
    display_mode: 'product_cutout_triptych'
  }
};
const STRICT_VISUALIZATION_CONSTRAINTS = {
  must_use_native_assets_first: true,
  allow_manual_draw: false,
  fallback_mode: 'summary_only',
  block_untrusted_local_render: true
};

export async function runSkillAction(params = {}, options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const emitStderr = options.emitStderr ?? defaultEmitStderr;
  const resolveAgentTaskAuthImpl = options.resolveAgentTaskAuthImpl ?? resolveAgentTaskAuth;
  const normalizeExecutePayloadImpl = options.normalizeExecutePayloadImpl ?? normalizeExecutePayload;
  const emitTelemetryImpl = options.emitTelemetryImpl ?? emitTelemetry;

  const action = typeof params.action === 'string' ? params.action.trim() : '';
  if (!ACTIONS[action]) {
    return createLocalResult(400, 'VALIDATION_BAD_REQUEST', `unsupported action: ${action || '<empty>'}`);
  }

  const payload = toObject(params.payload);
  const bridgeContext = extractBridgeContext(payload);
  const actionPayloadInput = stripBridgeContext(payload);

  let auth;
  try {
    auth = await resolveAgentTaskAuthImpl({
      baseUrl: params.baseUrl,
      ...bridgeContext
    });
  } catch (error) {
    return createLocalResult(
      Number.isFinite(error?.status) ? error.status : 401,
      typeof error?.code === 'string' ? error.code : 'AUTH_UNAUTHORIZED',
      asMessage(error)
    );
  }

  let request;
  try {
    request = await buildActionRequest(action, actionPayloadInput, normalizeExecutePayloadImpl, {
      auth,
      fetchImpl
    });
  } catch (error) {
    return createLocalResult(
      Number.isFinite(error?.status) ? error.status : 400,
      typeof error?.code === 'string' ? error.code : 'VALIDATION_BAD_REQUEST',
      asMessage(error),
      error?.details
    );
  }

  const usePublicBridge = auth?.mode === 'public_bridge' || !readText(auth?.agentTaskToken);
  const httpRequest = usePublicBridge ? buildPublicBridgeRequest(action, request.actionPayload, actionPayloadInput, auth) : request;

  const capability = action === 'portal.skill.execute' ? readText(request.body?.capability) : null;
  const runIdHint =
    action === 'portal.skill.poll' || action === 'portal.skill.presentation'
      ? resolveOptionalIdentifier(actionPayloadInput, ['run_id', 'runId'])
      : null;

  if (action === 'portal.skill.execute') {
    void emitTelemetryImpl({
      eventName: 'agent.execute.start',
      status: 'ok',
      capability: capability ?? undefined
    });
  } else if (action === 'portal.skill.poll') {
    void emitTelemetryImpl({
      eventName: 'agent.poll.start',
      status: 'ok',
      runId: runIdHint ?? undefined
    });
  }

  const response = await fetchImpl(`${auth.baseUrl}${httpRequest.path}`, {
    method: httpRequest.method,
    headers: {
      ...(usePublicBridge ? {} : { 'X-Agent-Task-Token': auth.agentTaskToken }),
      ...(httpRequest.method === 'POST' ? { 'Content-Type': 'application/json' } : {})
    },
    ...(httpRequest.body !== undefined ? { body: JSON.stringify(httpRequest.body) } : {})
  });

  const body = await response.text();
  const parsed = parseJson(body);
  let apiError = response.ok ? null : parseApiError(parsed, body, response.status);

  if (response.ok) {
    emitStderr({
      event: 'portal_action_success',
      action,
      status: response.status
    });
  } else {
    apiError = parseApiError(parsed, body, response.status);
    emitStderr({
      event: 'portal_action_failed',
      action,
      status: response.status,
      code: apiError.code,
      message: apiError.message,
      request_id: apiError.requestId
    });

    if (apiError.code === 'POINTS_INSUFFICIENT') {
      const rechargeUrl =
        parsed &&
        typeof parsed === 'object' &&
        parsed.error &&
        typeof parsed.error === 'object' &&
        parsed.error.details &&
        typeof parsed.error.details === 'object' &&
        typeof parsed.error.details.recharge_url === 'string'
          ? parsed.error.details.recharge_url
          : null;

      emitStderr({
        event: 'portal_action_recharge_hint',
        action,
        recharge_url: rechargeUrl,
        recommended_next_action: rechargeUrl ? 'open recharge_url' : 'contact host recharge entry'
      });
    }
  }

  const context = extractRequestContext(body);
  if (action === 'portal.skill.execute') {
    const actionApiError = response.ok ? null : parseApiError(parsed, body, response.status);
    void emitTelemetryImpl({
      eventName: response.ok ? 'agent.execute.success' : 'agent.execute.failed',
      status: response.ok ? 'ok' : 'error',
      capability: capability ?? undefined,
      runId: context.runId ?? undefined,
      requestId: context.requestId ?? actionApiError?.requestId ?? undefined,
      properties: response.ok
        ? {}
        : {
            code: actionApiError?.code,
            message: actionApiError?.message
          }
    });
  } else if (action === 'portal.skill.poll') {
    const actionApiError = response.ok ? null : parseApiError(parsed, body, response.status);
    void emitTelemetryImpl({
      eventName: response.ok ? 'agent.poll.terminal' : 'agent.poll.failed',
      status: response.ok ? 'ok' : 'error',
      runId: context.runId ?? runIdHint ?? undefined,
      requestId: context.requestId ?? actionApiError?.requestId ?? undefined,
      properties: response.ok
        ? {
            run_status: context.status
          }
        : {
            code: actionApiError?.code,
            message: actionApiError?.message
          }
    });
  }

  const responseBody = buildGuidedResponseBody({
    action,
    request: {
      ...request,
      path: httpRequest.path,
      method: httpRequest.method
    },
    ok: response.ok,
    parsed,
    body
  });

  return {
    ok: response.ok,
    status: response.status,
    body: responseBody
  };
}

async function buildActionRequest(action, payload, normalizeExecutePayloadImpl, context = {}) {
  switch (action) {
    case 'portal.skill.execute': {
      const preparedPayload = await prepareExecutePayload(payload, context);
      const normalized = await normalizeExecutePayloadImpl(preparedPayload);

      const capability = readRequiredString(normalized.capability, 'capability is required');
      const input = toObject(normalized.input);
      if (Object.keys(input).length === 0) {
        throw createActionError(400, 'VALIDATION_BAD_REQUEST', 'input must be an object');
      }

      const body = {
        capability,
        input
      };

      const requestId = typeof normalized.request_id === 'string' ? normalized.request_id.trim() : '';
      if (requestId) {
        body.request_id = requestId;
      }

      return {
        method: 'POST',
        path: '/agent/skill/execute',
        body,
        actionPayload: body
      };
    }
    case 'portal.skill.poll': {
      const runId = resolveIdentifier(payload, ['run_id', 'runId'], 'run_id is required');
      return {
        method: 'GET',
        path: `/agent/skill/runs/${encodeURIComponent(runId)}`,
        actionPayload: { run_id: runId }
      };
    }
    case 'portal.skill.presentation': {
      const runId = resolveIdentifier(payload, ['run_id', 'runId'], 'run_id is required');
      const includeFiles = payload.include_files === undefined ? true : payload.include_files;
      return {
        method: 'GET',
        path: buildPathWithQuery(`/agent/skill/runs/${encodeURIComponent(runId)}/presentation`, {
          channel: payload.channel,
          include_files: includeFiles
        }),
        actionPayload: {
          run_id: runId,
          ...(payload.channel !== undefined ? { channel: payload.channel } : {}),
          include_files: includeFiles
        }
      };
    }
    case 'portal.account.balance':
      return {
        method: 'GET',
        path: '/agent/skill/account/balance',
        actionPayload: {}
      };
    case 'portal.account.ledger':
      const dateRange = resolveDateRange(payload);
      return {
        method: 'GET',
        path: buildPathWithQuery('/agent/skill/account/ledger', dateRange),
        actionPayload: dateRange
      };
    default:
      throw createActionError(400, 'VALIDATION_BAD_REQUEST', `unsupported action: ${action}`);
  }
}

async function prepareExecutePayload(payload, context) {
  const candidate = await resolvePublicUploadCandidate(payload);
  if (!candidate) {
    return payload;
  }

  const auth = context?.auth;
  const fetchImpl = context?.fetchImpl;
  if (!auth || typeof auth !== 'object' || typeof fetchImpl !== 'function') {
    return payload;
  }

  const uploaded = await uploadCandidateThroughPublicBridge(candidate, auth, fetchImpl);
  return applyUploadedAttachment(payload, candidate, uploaded);
}

function buildPublicBridgeRequest(action, actionPayload, originalPayload, auth) {
  const body = {
    entry_host: auth.entryHost,
    action,
    agent_uid: auth.agentUid,
    conversation_id: auth.conversationId,
    payload: actionPayload
  };

  if (readText(auth.entryUserKey)) {
    body.entry_user_key = auth.entryUserKey;
  }

  const options =
    originalPayload?.options && typeof originalPayload.options === 'object' && !Array.isArray(originalPayload.options)
      ? originalPayload.options
      : null;
  if (options) {
    body.options = options;
  }

  return {
    method: 'POST',
    path: '/agent/public-bridge/invoke',
    body
  };
}

function extractBridgeContext(payload) {
  return {
    entryHost: resolveOptionalIdentifier(payload, ['entry_host', 'entryHost']) ?? undefined,
    entryUserKey: resolveOptionalIdentifier(payload, ['entry_user_key', 'entryUserKey']) ?? undefined,
    agentUid: resolveOptionalIdentifier(payload, ['agent_uid', 'agentUid']) ?? undefined,
    conversationId: resolveOptionalIdentifier(payload, ['conversation_id', 'conversationId']) ?? undefined
  };
}

function stripBridgeContext(payload) {
  const next = { ...payload };
  delete next.entry_host;
  delete next.entryHost;
  delete next.entry_user_key;
  delete next.entryUserKey;
  delete next.agent_uid;
  delete next.agentUid;
  delete next.conversation_id;
  delete next.conversationId;
  return next;
}

function buildPathWithQuery(path, query) {
  const entries = Object.entries(query).filter((entry) => {
    const value = entry[1];
    return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean';
  });
  if (entries.length === 0) {
    return path;
  }
  const search = new URLSearchParams();
  for (const [key, value] of entries) {
    search.set(key, String(value));
  }
  return `${path}?${search.toString()}`;
}

function readRequiredString(value, message) {
  if (typeof value !== 'string' || !value.trim()) {
    throw createActionError(400, 'VALIDATION_BAD_REQUEST', message);
  }
  return value.trim();
}

function resolveIdentifier(payload, keys, message) {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  throw createActionError(400, 'VALIDATION_BAD_REQUEST', message);
}

function resolveOptionalIdentifier(payload, keys) {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return null;
}

function resolveDateRange(payload) {
  const dateFrom = readOptionalDate(payload.date_from, 'date_from');
  const dateTo = readOptionalDate(payload.date_to, 'date_to');
  if (!dateFrom && !dateTo) {
    return {};
  }
  if (!dateFrom || !dateTo) {
    throw createActionError(400, 'VALIDATION_BAD_REQUEST', 'date_from and date_to are required together');
  }
  if (dateFrom > dateTo) {
    throw createActionError(400, 'VALIDATION_BAD_REQUEST', 'invalid date range');
  }
  return {
    date_from: dateFrom,
    date_to: dateTo
  };
}

function readOptionalDate(value, fieldName) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value.trim())) {
    throw createActionError(400, 'VALIDATION_BAD_REQUEST', `${fieldName} must use YYYY-MM-DD`);
  }
  return value.trim();
}

function readText(value) {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function createActionError(status, code, message, details) {
  const error = new Error(message);
  error.status = status;
  error.code = code;
  error.details = details;
  return error;
}

function createLocalResult(status, code, message, details = undefined) {
  const body = JSON.stringify({
    request_id: '',
    data: null,
    error: {
      code,
      message,
      ...(details ? { details } : {})
    }
  });

  return {
    ok: false,
    status,
    body
  };
}

function parseApiError(parsed, body, status) {
  const requestId = typeof parsed?.request_id === 'string' ? parsed.request_id : null;
  const error = parsed?.error;
  if (error && typeof error === 'object') {
    return {
      code: typeof error.code === 'string' ? error.code : `HTTP_${status}`,
      message: typeof error.message === 'string' ? error.message : body,
      requestId
    };
  }

  return {
    code: `HTTP_${status}`,
    message: body,
    requestId
  };
}

function parseJson(body) {
  try {
    const parsed = JSON.parse(body);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

function buildGuidedResponseBody({ action, request, ok, parsed, body }) {
  if (!ok || !parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return body;
  }

  const data = toObject(parsed.data);
  if (Object.keys(data).length === 0) {
    return body;
  }

  const guidance = buildAgentGuidance(action, request, data);
  if (!guidance) {
    return body;
  }

  const currentGuidance = toObject(data.agent_guidance);
  const enriched = {
    ...parsed,
    data: {
      ...data,
      agent_guidance: {
        ...currentGuidance,
        ...guidance
      }
    }
  };

  return JSON.stringify(enriched);
}

function buildAgentGuidance(action, request, data) {
  if (action === 'portal.skill.execute') {
    return buildExecuteGuidance(request, data);
  }
  if (action === 'portal.skill.poll') {
    return buildPollGuidance(data);
  }
  if (action === 'portal.skill.presentation') {
    return buildPresentationGuidance(data);
  }
  return null;
}

function buildExecuteGuidance(request, data) {
  const capability = readText(request?.actionPayload?.capability ?? request?.body?.capability);
  if (!capability || !IMAGE_CAPABILITIES.has(capability)) {
    return null;
  }

  const runId = resolveOptionalIdentifier(data, ['run_id', 'runId']);
  return {
    visualization: createVisualizationGuidance({
      runId,
      capability,
      source: 'execute'
    })
  };
}

function buildPollGuidance(data) {
  const runId = resolveOptionalIdentifier(data, ['run_id', 'runId']);
  const serviceId = readText(data.service_id);
  const output = data.output;
  const geometry = summarizeGeometry(output);

  if (!isLikelyVisualService(serviceId) && !hasAnyGeometry(geometry)) {
    return null;
  }

  return {
    visualization: createVisualizationGuidance({
      runId,
      serviceId,
      geometry,
      source: 'poll'
    })
  };
}

function buildPresentationGuidance(data) {
  const runId = resolveOptionalIdentifier(data, ['run_id', 'runId']);
  const serviceId = readText(data.service_id);
  const visual = toObject(data.visual);
  const spec = toObject(visual.spec);
  const geometry = summarizeGeometry(spec.layers ?? spec);
  const assets = summarizePresentationAssets(visual);

  if (!hasAnyGeometry(geometry) && !assets.available && !isLikelyVisualService(serviceId)) {
    return null;
  }

  return {
    visualization: createVisualizationGuidance({
      runId,
      serviceId,
      geometry,
      assets,
      source: 'presentation'
    })
  };
}

function createVisualizationGuidance({ runId, capability = null, serviceId = null, geometry = null, assets = null, source }) {
  const geometrySummary = geometry ?? { boxes: 0, points: 0, masks: 0 };
  const hasGeometry = hasAnyGeometry(geometrySummary);
  const playbook = resolveVisualizationPlaybook({
    capability,
    serviceId,
    geometry: geometrySummary,
    assets
  });

  const allowManualDraw = playbook?.rendering_constraints?.allow_manual_draw === true;

  return {
    source,
    ...(runId ? { run_id: runId } : {}),
    ...(capability ? { capability } : {}),
    ...(serviceId ? { service_id: serviceId } : {}),
    flow: buildVisualizationFlow({ runId, allowManualDraw }),
    detected_geometry: {
      boxes: geometrySummary.boxes,
      points: geometrySummary.points,
      masks: geometrySummary.masks,
      manual_primitives: resolveManualPrimitives(geometrySummary)
    },
    ...(assets?.available
      ? {
          rendered_assets: assets.byKind
        }
      : {}),
    ...(playbook
      ? {
          playbook
        }
      : {}),
    can_render_manually: hasGeometry && allowManualDraw
  };
}

function buildVisualizationFlow({ runId, allowManualDraw }) {
  const flow = [
    {
      step: 'fetch_rendered_assets',
      action: 'portal.skill.presentation',
      payload: {
        ...(runId ? { run_id: runId } : {}),
        include_files: true
      }
    },
    {
      step: 'asset_priority',
      kinds: GUIDANCE_ASSET_PRIORITY
    }
  ];

  if (allowManualDraw) {
    flow.push({
      step: 'manual_draw_fallback',
      coordinate_space: 'pixel',
      origin: 'top_left',
      bbox_fields: ['xmin', 'ymin', 'xmax', 'ymax'],
      point_fields: ['x', 'y'],
      score_fields: ['score', 'confidence'],
      default_min_score: 0.3
    });
    return flow;
  }

  flow.push({
    step: 'raw_summary_fallback',
    strategy: 'summarize_structured_output_only',
    allowed_sources: ['raw', 'visual.spec', 'visual.files'],
    forbid_local_manual_drawing: true
  });
  return flow;
}

function summarizePresentationAssets(visual) {
  const files = toObject(visual.files);
  const assetRows = Array.isArray(files.assets) ? files.assets : [];
  const byKind = {};

  for (const row of assetRows) {
    const asset = toObject(row);
    const kind = readText(asset.kind);
    const url = readText(asset.url);
    if (!kind || !url) {
      continue;
    }
    if (!Array.isArray(byKind[kind])) {
      byKind[kind] = [];
    }
    byKind[kind].push(url);
  }

  return {
    available: Object.keys(byKind).length > 0,
    byKind
  };
}

function summarizeGeometry(input) {
  const summary = {
    boxes: 0,
    points: 0,
    masks: 0
  };
  visitGeometry(input, summary, 0);
  return summary;
}

function visitGeometry(value, summary, depth) {
  if (depth > 8 || value === null || value === undefined) {
    return;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      visitGeometry(item, summary, depth + 1);
    }
    return;
  }

  if (typeof value !== 'object') {
    return;
  }

  const record = value;
  if (isBoxRecord(record)) {
    summary.boxes += 1;
  }
  if (isPointRecord(record)) {
    summary.points += 1;
  }
  if (isMaskRecord(record)) {
    summary.masks += 1;
  }

  for (const nested of Object.values(record)) {
    visitGeometry(nested, summary, depth + 1);
  }
}

function isBoxRecord(record) {
  return (
    (hasFinite(record, 'xmin') && hasFinite(record, 'ymin') && hasFinite(record, 'xmax') && hasFinite(record, 'ymax')) ||
    (hasFinite(record, 'x') && hasFinite(record, 'y') && hasFinite(record, 'width') && hasFinite(record, 'height'))
  );
}

function isPointRecord(record) {
  if (!hasFinite(record, 'x') || !hasFinite(record, 'y')) {
    return false;
  }
  return !('width' in record || 'height' in record || 'xmin' in record || 'xmax' in record || 'ymin' in record || 'ymax' in record);
}

function isMaskRecord(record) {
  const kind = readText(record.kind);
  if (kind === 'mask' || kind === 'segmentation' || kind === 'confidence') {
    return true;
  }
  const dataUrl = readText(record.data_url);
  return typeof dataUrl === 'string' && dataUrl.startsWith('data:image/');
}

function hasFinite(record, key) {
  return typeof record[key] === 'number' && Number.isFinite(record[key]);
}

function hasAnyGeometry(geometry) {
  return geometry.boxes > 0 || geometry.points > 0 || geometry.masks > 0;
}

function resolveManualPrimitives(geometry) {
  const primitives = [];
  if (geometry.boxes > 0) {
    primitives.push('bbox_xyxy');
  }
  if (geometry.points > 0) {
    primitives.push('keypoint_xy');
  }
  if (geometry.masks > 0) {
    primitives.push('mask_alpha');
  }
  return primitives;
}

function resolveVisualizationPlaybook({ capability, serviceId, geometry, assets }) {
  const resolvedCapability = capability ?? resolveCapabilityByServiceId(serviceId);
  if (!resolvedCapability) {
    return null;
  }

  const presetName = VISUAL_PLAYBOOK_PRESET_BY_CAPABILITY[resolvedCapability];
  if (!presetName) {
    return null;
  }
  const preset = VISUAL_PLAYBOOK_PRESETS[presetName];
  if (!preset) {
    return null;
  }
  const overrides = VISUAL_PLAYBOOK_OVERRIDES[resolvedCapability] ?? {};

  const hasGeometry = hasAnyGeometry(geometry);
  const hasRenderedAssets = Boolean(assets?.available);

  const preferredAssets = Array.isArray(overrides.preferred_assets)
    ? overrides.preferred_assets
    : preset.preferred_assets;
  const summaryFields = Array.isArray(overrides.summary_fields)
    ? overrides.summary_fields
    : preset.summary_fields;
  const qualityChecks = Array.isArray(overrides.quality_checks)
    ? overrides.quality_checks
    : preset.quality_checks;

  return {
    capability: resolvedCapability,
    display_mode: overrides.display_mode ?? preset.display_mode,
    preferred_assets: preferredAssets,
    summary_fields: summaryFields,
    ...(qualityChecks ? { quality_checks: qualityChecks } : {}),
    chat_template: overrides.chat_template ?? preset.chat_template,
    ...(overrides.fallback_capability ? { fallback_capability: overrides.fallback_capability } : {}),
    rendering_constraints: {
      ...STRICT_VISUALIZATION_CONSTRAINTS
    },
    runtime_hints: {
      has_rendered_assets: hasRenderedAssets,
      has_geometry: hasGeometry
    },
    ...(resolvedCapability === 'body-contour-63pt' && !hasRenderedAssets && !hasGeometry
      ? {
          status: 'degraded',
          recommended_fallback_capability: 'body-keypoints-2d',
          recommended_next_action: 'rerun_with_body-keypoints-2d'
        }
      : {})
  };
}

function resolveCapabilityByServiceId(serviceId) {
  if (!serviceId || typeof serviceId !== 'string') {
    return null;
  }
  const capability = SERVICE_CAPABILITY_HINTS[serviceId];
  return typeof capability === 'string' ? capability : null;
}

function isLikelyVisualService(serviceId) {
  return Boolean(serviceId) && !NON_VISUAL_SERVICE_IDS.has(serviceId);
}

function toObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {};
  }
  return { ...value };
}

function defaultEmitStderr(event) {
  process.stderr.write(`${JSON.stringify(event)}\n`);
}

function asMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function parseCliArgs(args) {
  if (args.length === 0) {
    return {
      action: 'portal.skill.execute',
      payloadJson: '{}',
      baseUrl: AGENT_TASK_DEFAULT_BASE_URL
    };
  }

  const first = args[0] ?? '';
  const firstLooksLikeAction = Boolean(ACTIONS[first]);
  const second = args[1] ?? '';
  const secondLooksLikeAction = Boolean(ACTIONS[second]);

  if (!firstLooksLikeAction && secondLooksLikeAction) {
    return {
      action: first,
      payloadJson: args[2] ?? '{}',
      baseUrl: args[3] ?? AGENT_TASK_DEFAULT_BASE_URL
    };
  }

  return {
    action: first,
    payloadJson: args[1] ?? '{}',
    baseUrl: args[2] ?? AGENT_TASK_DEFAULT_BASE_URL
  };
}

async function main() {
  const parsed = parseCliArgs(process.argv.slice(2));

  let payload;
  try {
    payload = JSON.parse(parsed.payloadJson);
  } catch {
    const result = createLocalResult(400, 'VALIDATION_BAD_REQUEST', 'payload_json must be valid JSON object');
    process.stdout.write(`${result.body}\n`);
    process.exit(1);
  }

  const result = await runSkillAction({
    action: parsed.action,
    payload,
    baseUrl: parsed.baseUrl
  });

  process.stdout.write(`${result.body}\n`);
  if (!result.ok) {
    process.exit(1);
  }
}

const importedScriptName = basename(fileURLToPath(import.meta.url));
const invokedScriptName = process.argv[1] ? basename(process.argv[1]) : '';

if (
  process.argv[1] &&
  (import.meta.url === pathToFileURL(process.argv[1]).href || invokedScriptName === importedScriptName)
) {
  await main();
}
