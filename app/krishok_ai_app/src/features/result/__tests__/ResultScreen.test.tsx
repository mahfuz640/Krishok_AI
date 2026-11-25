import { render, waitFor } from '@testing-library/react-native';
import ResultScreen from '@/app/result';

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
  useLocalSearchParams: () => ({ imageUri: 'file://unclassified-leaf.jpg' }),
}));
jest.mock('@/core/ai/detectionService', () => {
  const { DetectionServiceError } = require('@/core/ai/errors');
  return {
    detectDisease: jest.fn().mockRejectedValue(new DetectionServiceError('OFFLINE_NOT_READY')),
  };
});

describe('result error state', () => {
  it('states that no prediction was made when the model is unavailable', async () => {
    const view = await render(<ResultScreen />);
    await waitFor(() => expect(view.getByText('রোগের কোনো পূর্বাভাস দেওয়া হয়নি')).toBeTruthy());
    expect(view.queryByText('ব্লাস্ট')).toBeNull();
  });
});
