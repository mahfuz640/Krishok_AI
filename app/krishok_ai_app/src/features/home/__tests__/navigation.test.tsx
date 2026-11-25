import { fireEvent, render } from '@testing-library/react-native';
import HomeScreen from '@/app/(tabs)/index';

jest.mock('expo-router', () => {
  const router = { push: jest.fn(), replace: jest.fn(), back: jest.fn() };
  return { useRouter: () => router, __router: router };
});

describe('home navigation', () => {
  it('opens the scanner from the main action', async () => {
    const view = await render(<HomeScreen />);
    fireEvent.press(view.getByRole('button', { name: 'স্ক্যানার খুলুন' }));
    expect(require('expo-router').__router.push).toHaveBeenCalledWith('/scanner');
  });
});
