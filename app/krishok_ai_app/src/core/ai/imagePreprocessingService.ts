import { DetectionServiceError } from './errors';
import type { ImagePreprocessingService } from './contracts';

export interface CroppedRgb224Decoder {
  /** Decode, orient, bilinear-resize (short edge 232, antialias), center crop to 224, and return packed RGB bytes. */
  decodeRiceLeaf224(imageUri: string): Promise<Uint8Array>;
}

export function normalizeRgb224ToNhwc(rgb: Uint8Array): Float32Array {
  const pixels = 224 * 224;
  if (rgb.length !== pixels * 3) {
    throw new DetectionServiceError(
      'INVALID_IMAGE',
      `Expected ${pixels * 3} RGB bytes, received ${rgb.length}.`,
    );
  }
  const means = [0.485, 0.456, 0.406];
  const stds = [0.229, 0.224, 0.225];
  const output = new Float32Array(rgb.length);
  for (let i = 0; i < pixels; i += 1) {
    const offset = i * 3;
    output[offset] = (rgb[offset] / 255 - means[0]) / stds[0];
    output[offset + 1] = (rgb[offset + 1] / 255 - means[1]) / stds[1];
    output[offset + 2] = (rgb[offset + 2] / 255 - means[2]) / stds[2];
  }
  return output;
}

export class RiceLeafImagePreprocessingService implements ImagePreprocessingService {
  constructor(private readonly decoder?: CroppedRgb224Decoder) {}

  async prepare(imageUri: string): Promise<Float32Array> {
    if (!imageUri) throw new DetectionServiceError('INVALID_IMAGE');
    if (!this.decoder)
      throw new DetectionServiceError(
        'OFFLINE_NOT_READY',
        'Native pixel decoder is not configured.',
      );
    try {
      return normalizeRgb224ToNhwc(await this.decoder.decodeRiceLeaf224(imageUri));
    } catch (error) {
      if (error instanceof DetectionServiceError) throw error;
      throw new DetectionServiceError('INVALID_IMAGE', 'Image decode or preprocessing failed.', {
        cause: error,
      });
    }
  }
}
