export type DetectionErrorCode =
  | 'ONLINE_NOT_CONFIGURED'
  | 'OFFLINE_NOT_READY'
  | 'INVALID_IMAGE'
  | 'INVALID_RESPONSE'
  | 'INFERENCE_FAILED';

export class DetectionServiceError extends Error {
  constructor(
    public readonly code: DetectionErrorCode,
    message?: string,
    options?: ErrorOptions,
  ) {
    super(message ?? code, options);
    this.name = 'DetectionServiceError';
  }
}
