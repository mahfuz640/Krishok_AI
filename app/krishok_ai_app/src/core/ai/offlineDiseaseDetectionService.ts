import type {
  DiseaseDetectionService,
  ImagePreprocessingService,
  TfliteModelRunner,
} from './contracts';
import { DetectionServiceError } from './errors';
import { predictionFromLogits } from './prediction';

export class OfflineDiseaseDetectionService implements DiseaseDetectionService {
  constructor(
    private readonly runner?: TfliteModelRunner,
    private readonly preprocessor?: ImagePreprocessingService,
  ) {}

  async detect({ imageUri }: { imageUri: string; mode: 'offline' }) {
    if (!this.runner || !this.preprocessor) throw new DetectionServiceError('OFFLINE_NOT_READY');
    try {
      const input = await this.preprocessor.prepare(imageUri);
      const logits = await this.runner.run(input);
      return predictionFromLogits(logits, 'offline');
    } catch (error) {
      if (error instanceof DetectionServiceError) throw error;
      throw new DetectionServiceError('INFERENCE_FAILED', 'Offline inference failed.', {
        cause: error,
      });
    }
  }
}
