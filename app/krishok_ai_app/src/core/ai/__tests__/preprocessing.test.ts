import { normalizeRgb224ToNhwc } from '../imagePreprocessingService';

describe('rice image normalization', () => {
  it('creates an NHWC float32 tensor using the checkpoint normalization', () => {
    const rgb = new Uint8Array(224 * 224 * 3);
    rgb.set([255, 0, 127]);
    const tensor = normalizeRgb224ToNhwc(rgb);
    expect(tensor).toHaveLength(224 * 224 * 3);
    expect(tensor[0]).toBeCloseTo((1 - 0.485) / 0.229, 5);
    expect(tensor[1]).toBeCloseTo((0 - 0.456) / 0.224, 5);
    expect(tensor[2]).toBeCloseTo((127 / 255 - 0.406) / 0.225, 5);
  });

  it('rejects an image buffer with the wrong shape', () => {
    expect(() => normalizeRgb224ToNhwc(new Uint8Array(8))).toThrow('Expected');
  });
});
