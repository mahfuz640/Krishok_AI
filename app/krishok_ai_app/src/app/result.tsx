import { useEffect, useState } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { PrimaryButton } from '@/components/PrimaryButton';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { detectDisease } from '@/core/ai/detectionService';
import { DetectionServiceError } from '@/core/ai/errors';
import { useAppStore } from '@/core/store/useAppStore';
import { detectionHistoryRepository } from '@/data/historyRepository';
import type { PredictionResult } from '@/domain/disease';
import { DISEASE_CLASSES } from '@/domain/disease';
import { colors, radius, spacing } from '@/core/theme';

export default function ResultScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useLocalSearchParams<{ imageUri?: string }>();
  const imageUri = typeof params.imageUri === 'string' ? params.imageUri : '';
  const mode = useAppStore((state) => state.detectionMode);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const detect = async () => {
      if (!imageUri) {
        setError(t('errors.invalidImage'));
        return;
      }
      setLoading(true);
      try {
        const result = await detectDisease({ imageUri, mode });
        if (!active) return;
        await detectionHistoryRepository.add({
          imageUri,
          createdAt: result.createdAt,
          predictedClassId: result.classId,
          confidence: result.confidence,
          mode,
        });
        setPrediction(result);
      } catch (cause) {
        if (!active) return;
        if (cause instanceof DetectionServiceError && cause.code === 'ONLINE_NOT_CONFIGURED')
          setError(t('errors.onlineNotConfigured'));
        else if (cause instanceof DetectionServiceError && cause.code === 'INVALID_IMAGE')
          setError(t('errors.invalidImage'));
        else if (
          cause instanceof DetectionServiceError &&
          (cause.code === 'OFFLINE_NOT_READY' || cause.code === 'INFERENCE_FAILED')
        )
          setError(t('errors.offlineNotReady'));
        else setError(t('errors.generic'));
      } finally {
        if (active) setLoading(false);
      }
    };
    void detect();
    return () => {
      active = false;
    };
  }, [imageUri, mode, t]);

  const selected = prediction ? DISEASE_CLASSES[prediction.classId] : null;
  return (
    <Screen>
      <ScreenHeader title={t('result.title')} />
      {imageUri ? (
        <Image
          accessibilityLabel={t('result.photoLabel')}
          source={{ uri: imageUri }}
          style={styles.photo}
        />
      ) : null}
      {loading ? (
        <SurfaceCard style={styles.loading}>
          <AppText>{t('common.loading')}</AppText>
        </SurfaceCard>
      ) : null}
      {!loading && !prediction ? (
        <Notice
          title={t('result.noPredictionTitle')}
          body={error ? `${t('result.noPredictionBody')} ${error}` : t('result.noPredictionBody')}
          tone="warning"
        />
      ) : null}
      {prediction && selected ? (
        <SurfaceCard>
          <View style={styles.predictionIcon}>
            <Ionicons name="leaf" size={27} color={colors.primary} />
          </View>
          <AppText variant="caption" style={styles.muted}>
            {t('result.title')}
          </AppText>
          <AppText variant="heading">{t(`disease.${selected.key}`)}</AppText>
          <AppText style={styles.muted}>{Math.round(prediction.confidence * 100)}%</AppText>
        </SurfaceCard>
      ) : null}
      <SurfaceCard>
        <AppText variant="bodyStrong">{t('result.next')}</AppText>
        <AppText style={styles.muted}>{t('result.nextBody')}</AppText>
      </SurfaceCard>
      <PrimaryButton
        label={t('result.diseaseGuide')}
        icon="book-outline"
        onPress={() => router.push('/disease')}
      />
      <PrimaryButton
        label={t('result.scanAnother')}
        icon="camera"
        secondary
        onPress={() => router.replace('/scanner')}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  photo: {
    width: '100%',
    height: 260,
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceMuted,
  },
  loading: { alignItems: 'center', paddingVertical: spacing.lg },
  predictionIcon: {
    width: 54,
    height: 54,
    borderRadius: 18,
    backgroundColor: '#EAF3DE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  muted: { color: colors.textMuted },
});
