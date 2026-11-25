import { fireEvent, render, waitFor } from '@testing-library/react-native';
import HistoryScreen from '@/app/(tabs)/history';

jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
    useFocusEffect: (callback: () => void | (() => void)) => React.useEffect(callback, [callback]),
  };
});
jest.mock('@/data/historyRepository', () => ({
  detectionHistoryRepository: { list: jest.fn(), clear: jest.fn(), add: jest.fn() },
}));

const repository = require('@/data/historyRepository').detectionHistoryRepository as {
  list: jest.Mock;
  clear: jest.Mock;
  add: jest.Mock;
};

describe('history empty and error states', () => {
  beforeEach(() => {
    repository.list.mockResolvedValue([]);
  });

  it('shows an empty state when SQLite contains no detections', async () => {
    const view = await render(<HistoryScreen />);
    await waitFor(() => expect(view.getByText('এখনো কোনো পরীক্ষা সংরক্ষিত নেই')).toBeTruthy());
  });

  it('shows a recoverable storage error when the read fails', async () => {
    repository.list.mockRejectedValueOnce(new Error('db unavailable'));
    const view = await render(<HistoryScreen />);
    await waitFor(() =>
      expect(
        view.getByText('স্থানীয় স্টোরেজ পাওয়া যাচ্ছে না। পছন্দ সংরক্ষিত নাও থাকতে পারে।'),
      ).toBeTruthy(),
    );
    fireEvent.press(view.getByText('আবার চেষ্টা করুন'));
  });
});
