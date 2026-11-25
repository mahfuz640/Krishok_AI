import { fireEvent, render } from '@testing-library/react-native';
import CameraScreen from '@/app/camera';

jest.mock('expo-router', () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
}));
jest.mock('expo-camera', () => {
  const React = require('react');
  const ReactNative = require('react-native');
  const requestPermission = jest.fn();
  return {
    CameraView: React.forwardRef(function MockCameraView(_props: object, _ref: unknown) {
      return React.createElement(ReactNative.View, { testID: 'camera-preview' });
    }),
    useCameraPermissions: () => [{ granted: false, canAskAgain: true }, requestPermission],
    __requestPermission: requestPermission,
  };
});

describe('camera permission handling', () => {
  it('explains why camera permission is needed and requests it on action', async () => {
    const view = await render(<CameraScreen />);
    expect(view.getByText('ক্যামেরার অনুমতি দরকার')).toBeTruthy();
    fireEvent.press(view.getByRole('button', { name: 'ক্যামেরার অনুমতি দিন' }));
    expect(require('expo-camera').__requestPermission).toHaveBeenCalledTimes(1);
  });
});
