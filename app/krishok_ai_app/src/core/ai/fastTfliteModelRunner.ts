import { loadTensorflowModel, type ModelSource } from 'react-native-fast-tflite';
import type { TfliteModelRunner } from './contracts';
import { DetectionServiceError } from './errors';

/** Native LiteRT adapter. It deliberately requires an explicit, app-local model URI. */
export class FastTfliteModelRunner implements TfliteModelRunner {
  private model: Awaited<ReturnType<typeof loadTensorflowModel>> | null = null;

  constructor(private readonly localModelUri?: string) {}

  async load(): Promise<void> {
    if (!this.localModelUri || !this.localModelUri.startsWith('file://')) {
      throw new DetectionServiceError(
        'OFFLINE_NOT_READY',
        'A verified local TFLite model file has not been configured.',
      );
    }
    try {
      const source: ModelSource = { url: this.localModelUri };
      this.model = await loadTensorflowModel(source, []);
      const input = this.model.inputs[0];
      if (input?.dataType !== 'float32' || input.shape.join(',') !== '1,224,224,3') {
        this.model = null;
        throw new DetectionServiceError(
          'INFERENCE_FAILED',
          'TFLite input contract does not match the verified model metadata.',
        );
      }
    } catch (error) {
      if (error instanceof DetectionServiceError) throw error;
      throw new DetectionServiceError(
        'OFFLINE_NOT_READY',
        'Native TFLite runtime could not load the model.',
        { cause: error },
      );
    }
  }

  async run(input: Float32Array): Promise<Float32Array> {
    if (!this.model) await this.load();
    if (!this.model || input.length !== 224 * 224 * 3)
      throw new DetectionServiceError('INVALID_IMAGE');
    const buffer = input.buffer.slice(
      input.byteOffset,
      input.byteOffset + input.byteLength,
    ) as ArrayBuffer;
    const outputs = await this.model.run([buffer]);
    if (!outputs[0])
      throw new DetectionServiceError(
        'INFERENCE_FAILED',
        'The model did not return output logits.',
      );
    return new Float32Array(outputs[0]);
  }
}
