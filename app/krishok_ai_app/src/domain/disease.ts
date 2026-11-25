export const DISEASE_CLASSES = [
  { id: 0, key: 'blast', label: 'Blast' },
  { id: 1, key: 'brownSpot', label: 'Brown spot' },
  { id: 2, key: 'healthy', label: 'Healthy' },
  { id: 3, key: 'leafSmut', label: 'Leaf smut' },
  { id: 4, key: 'tungro', label: 'Rice Tungro' },
  { id: 5, key: 'sheathBlight', label: 'Sheath blight' },
] as const;

export type DiseaseClassId = (typeof DISEASE_CLASSES)[number]['id'];
export type DetectionMode = 'online' | 'offline';

export interface PredictionResult {
  classId: DiseaseClassId;
  diseaseName: (typeof DISEASE_CLASSES)[number]['label'];
  confidence: number;
  createdAt: string;
  modelVersion: string;
  mode: DetectionMode;
}

export function isDiseaseClassId(value: number): value is DiseaseClassId {
  return Number.isInteger(value) && value >= 0 && value < DISEASE_CLASSES.length;
}

export function normalizePrediction(
  classId: number,
  confidence: number,
  mode: DetectionMode,
): PredictionResult {
  if (
    !isDiseaseClassId(classId) ||
    !Number.isFinite(confidence) ||
    confidence < 0 ||
    confidence > 1
  ) {
    throw new Error('InvalidPrediction');
  }
  const disease = DISEASE_CLASSES[classId];
  return {
    classId: disease.id,
    diseaseName: disease.label,
    confidence,
    createdAt: new Date().toISOString(),
    modelVersion: 'mobilenetv3-large-rice-provisional',
    mode,
  };
}
