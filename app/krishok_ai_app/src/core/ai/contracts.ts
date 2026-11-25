import type { DetectionMode, PredictionResult } from '@/domain/disease';

export interface DiseaseDetectionRequest {
  imageUri: string;
  mode: DetectionMode;
}

export interface DiseaseDetectionService {
  detect(request: DiseaseDetectionRequest): Promise<PredictionResult>;
}

export interface ImagePreprocessingService {
  prepare(imageUri: string): Promise<Float32Array>;
}

export interface TfliteModelRunner {
  run(input: Float32Array): Promise<Float32Array>;
}
