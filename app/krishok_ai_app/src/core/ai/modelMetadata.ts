import { DISEASE_CLASSES } from '@/domain/disease';

export const modelMetadata = {
  name: 'MobileNetV3-Large',
  crop: 'rice',
  version: 'provisional-primary',
  input: { shape: [1, 224, 224, 3] as const, layout: 'NHWC', dtype: 'float32' },
  preprocessing: {
    color: 'RGB',
    resizeShorterEdge: 232,
    interpolation: 'bilinear',
    centerCrop: [224, 224] as const,
    scale: 'uint8 / 255',
    mean: [0.485, 0.456, 0.406] as const,
    std: [0.229, 0.224, 0.225] as const,
  },
  classes: DISEASE_CLASSES,
  artifact:
    'AI/experiments/MobileNetV3_Rice/deployment/tflite_fp32/mobilenetv3_large_fp32_float32.tflite',
  artifactPackaged: false,
  verification:
    'Validated with TensorFlow Lite CPU on Windows; Android/iOS native runtime not device-verified.',
} as const;
