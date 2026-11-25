import * as ImagePicker from 'expo-image-picker';
import { pickRiceLeafImage } from '../galleryPicker';

jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));

describe('gallery picker', () => {
  it('returns a selected image URI', async () => {
    jest.mocked(ImagePicker.launchImageLibraryAsync).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://leaf.jpg' }],
    } as ImagePicker.ImagePickerResult);
    await expect(pickRiceLeafImage()).resolves.toEqual({
      status: 'selected',
      uri: 'file://leaf.jpg',
    });
    expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith(
      expect.objectContaining({ mediaTypes: ['images'], quality: 1 }),
    );
  });

  it('returns a canceled result without creating a prediction', async () => {
    jest
      .mocked(ImagePicker.launchImageLibraryAsync)
      .mockResolvedValue({ canceled: true, assets: null } as ImagePicker.ImagePickerResult);
    await expect(pickRiceLeafImage()).resolves.toEqual({ status: 'cancelled' });
  });
});
