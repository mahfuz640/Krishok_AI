import { DISEASE_CLASSES, normalizePrediction } from '@/domain/disease';
import { predictionFromLogits } from '../prediction';
import { OfflineDiseaseDetectionService } from '../offlineDiseaseDetectionService';

describe('approved disease classes and prediction validation', () => {
  it('keeps the approved class id order intact', () => {
    expect(DISEASE_CLASSES.map(({ id, label }) => [id, label])).toEqual([
      [0, 'Blast'],
      [1, 'Brown spot'],
      [2, 'Healthy'],
      [3, 'Leaf smut'],
      [4, 'Rice Tungro'],
      [5, 'Sheath blight'],
    ]);
  });

  it('converts logits into a finite confidence score', () => {
    const prediction = predictionFromLogits(new Float32Array([0, 0, 4, 1, -1, 0]), 'offline');
    expect(prediction.classId).toBe(2);
    expect(prediction.confidence).toBeGreaterThan(0.89);
    expect(prediction.confidence).toBeLessThanOrEqual(1);
  });

  it('rejects an invalid confidence value', () => {
    expect(() => normalizePrediction(0, 1.1, 'offline')).toThrow('InvalidPrediction');
  });

  it('returns an explicit unavailable error when no offline model runner exists', async () => {
    await expect(
      new OfflineDiseaseDetectionService().detect({ imageUri: 'file://leaf.jpg', mode: 'offline' }),
    ).rejects.toMatchObject({ code: 'OFFLINE_NOT_READY' });
  });
});
