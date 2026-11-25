import { render } from '@testing-library/react-native';
import SplashRoute from '@/app/index';

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
}));

describe('application startup screen', () => {
  it('renders Krishok AI and a usable first action', async () => {
    const view = await render(<SplashRoute />);
    expect(view.getByText('Krishok AI')).toBeTruthy();
    expect(view.getByRole('button', { name: 'শুরু করুন' })).toBeTruthy();
  });
});
