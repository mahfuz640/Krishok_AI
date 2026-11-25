import * as ImagePicker from 'expo-image-picker';

export type GallerySelection = { status: 'selected'; uri: string } | { status: 'cancelled' };

export async function pickRiceLeafImage(): Promise<GallerySelection> {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsEditing: false,
    quality: 1,
    exif: false,
  });
  if (result.canceled || !result.assets[0]) return { status: 'cancelled' };
  return { status: 'selected', uri: result.assets[0].uri };
}
