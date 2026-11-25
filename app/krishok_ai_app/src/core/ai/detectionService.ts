import Constants from 'expo-constants';
import type { PredictionResult } from '@/domain/disease';
import type { DiseaseDetectionRequest } from './contracts';
import { OfflineDiseaseDetectionService } from './offlineDiseaseDetectionService';
import { OnlineDiseaseDetectionService } from './onlineDiseaseDetectionService';
import { FastTfliteModelRunner } from './fastTfliteModelRunner';
import { RiceLeafImagePreprocessingService } from './imagePreprocessingService';

const extra = Constants.expoConfig?.extra as
  { onlineApiBaseUrl?: string; offlineModelUri?: string } | undefined;
const offlineService = new OfflineDiseaseDetectionService(
  new FastTfliteModelRunner(extra?.offlineModelUri),
  new RiceLeafImagePreprocessingService(),
);
const onlineService = new OnlineDiseaseDetectionService(extra?.onlineApiBaseUrl);

export function detectDisease(request: DiseaseDetectionRequest): Promise<PredictionResult> {
  return request.mode === 'online'
    ? onlineService.detect({ ...request, mode: 'online' })
    : offlineService.detect({ ...request, mode: 'offline' });
}
