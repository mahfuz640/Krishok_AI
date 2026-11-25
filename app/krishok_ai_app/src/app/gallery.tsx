import { useState } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { Notice } from '@/components/Notice';
import { PrimaryButton } from '@/components/PrimaryButton';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { colors, radius } from '@/core/theme';
import { pickRiceLeafImage } from '@/features/media/galleryPicker';

export default function GalleryScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const pick = async () => {
    setError('');
    setLoading(true);
    try {
      const result = await pickRiceLeafImage();
      if (result.status === 'selected') {
        setPreview(result.uri);
        router.replace({ pathname: '/result', params: { imageUri: result.uri } });
      }
    } catch {
      setError(t('gallery.error'));
    } finally {
      setLoading(false);
    }
  };
  return (
    <Screen contentStyle={styles.page}>
      <ScreenHeader title={t('gallery.title')} subtitle={t('gallery.subtitle')} />
      <View style={styles.preview}>
        {preview ? (
          <Image source={{ uri: preview }} style={StyleSheet.absoluteFill} />
        ) : (
          <Ionicons name="image-outline" size={56} color={colors.primary} />
        )}
      </View>
      {error ? <Notice title={t('errors.generic')} body={error} tone="error" /> : null}
      <PrimaryButton
        label={t('gallery.open')}
        icon="images"
        onPress={() => void pick()}
        loading={loading}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1 },
  preview: {
    flex: 1,
    minHeight: 300,
    maxHeight: 450,
    borderRadius: radius.lg,
    backgroundColor: '#E6EFDF',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
});
