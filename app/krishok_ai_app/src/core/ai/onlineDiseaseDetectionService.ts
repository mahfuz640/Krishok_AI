import type { DiseaseDetectionService } from './contracts';
import { normalizePrediction } from '@/domain/disease';
import { DetectionServiceError } from './errors';

export class OnlineDiseaseDetectionService implements DiseaseDetectionService {
  constructor(private readonly endpoint?: string) {}

  async detect({ imageUri, mode }: { imageUri: string; mode: 'online' }) {
    if (!this.endpoint) throw new DetectionServiceError('ONLINE_NOT_CONFIGURED');
    if (!imageUri) throw new DetectionServiceError('INVALID_IMAGE');
    const data = new FormData();
    data.append('image', {
      uri: imageUri,
      name: 'rice-leaf.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    let response: Response;
    try {
      response = await fetch(`${this.endpoint.replace(/\/$/, '')}/v1/rice/detect`, {
        method: 'POST',
        body: data,
      });
    } catch (error) {
      throw new DetectionServiceError('INFERENCE_FAILED', 'Online detection request failed.', {
        cause: error,
      });
    }
    if (!response.ok)
      throw new DetectionServiceError(
        'INFERENCE_FAILED',
        `Detection server responded with ${response.status}.`,
      );
    const payload: unknown = await response.json();
    if (
      !payload ||
      typeof payload !== 'object' ||
      !('classId' in payload) ||
      !('confidence' in payload) ||
      typeof payload.classId !== 'number' ||
      typeof payload.confidence !== 'number'
    ) {
      throw new DetectionServiceError('INVALID_RESPONSE');
    }
    try {
      return normalizePrediction(payload.classId, payload.confidence, mode);
    } catch (error) {
      throw new DetectionServiceError(
        'INVALID_RESPONSE',
        'Detection server returned an invalid prediction.',
        { cause: error },
      );
    }
  }
}
