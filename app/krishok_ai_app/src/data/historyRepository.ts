import type { DetectionMode, DiseaseClassId } from '@/domain/disease';
import { getLocalDatabase } from './localDatabase';

export interface DetectionHistoryRecord {
  id: number;
  imageUri: string;
  createdAt: string;
  predictedClassId: DiseaseClassId;
  confidence: number;
  mode: DetectionMode;
}

export type NewDetectionHistoryRecord = Omit<DetectionHistoryRecord, 'id'>;

export interface DetectionHistoryRepository {
  add(record: NewDetectionHistoryRecord): Promise<number>;
  list(): Promise<DetectionHistoryRecord[]>;
  clear(): Promise<void>;
}

export const detectionHistoryRepository: DetectionHistoryRepository = {
  async add(record) {
    const db = await getLocalDatabase();
    const result = await db.runAsync(
      'INSERT INTO detection_history (image_uri, created_at, predicted_class_id, confidence, mode) VALUES (?, ?, ?, ?, ?)',
      record.imageUri,
      record.createdAt,
      record.predictedClassId,
      record.confidence,
      record.mode,
    );
    return result.lastInsertRowId;
  },
  async list() {
    const db = await getLocalDatabase();
    const rows = await db.getAllAsync<{
      id: number;
      image_uri: string;
      created_at: string;
      predicted_class_id: number;
      confidence: number;
      mode: DetectionMode;
    }>(
      'SELECT id, image_uri, created_at, predicted_class_id, confidence, mode FROM detection_history ORDER BY created_at DESC',
    );
    return rows.map((row) => ({
      id: row.id,
      imageUri: row.image_uri,
      createdAt: row.created_at,
      predictedClassId: row.predicted_class_id as DiseaseClassId,
      confidence: row.confidence,
      mode: row.mode,
    }));
  },
  async clear() {
    const db = await getLocalDatabase();
    await db.runAsync('DELETE FROM detection_history');
  },
};
