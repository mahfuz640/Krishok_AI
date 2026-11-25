import { normalizePrediction, type DetectionMode, type PredictionResult } from '@/domain/disease';
import { DetectionServiceError } from './errors';

export function predictionFromLogits(logits: Float32Array, mode: DetectionMode): PredictionResult {
  if (logits.length !== 6 || [...logits].some((value) => !Number.isFinite(value))) {
    throw new DetectionServiceError('INFERENCE_FAILED', 'The model returned invalid logits.');
  }
  const max = Math.max(...logits);
  const exponents = [...logits].map((value) => Math.exp(value - max));
  const total = exponents.reduce((sum, value) => sum + value, 0);
  const classId = logits.indexOf(max);
  return normalizePrediction(classId, exponents[classId] / total, mode);
}
