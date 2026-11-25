import { useCallback, useState } from 'react';
import { Alert, Image, Pressable, StyleSheet, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Screen } from '@/components/Screen';
import { SurfaceCard } from '@/components/SurfaceCard';
import { ScreenHeader } from '@/components/ScreenHeader';
import { colors, radius, spacing } from '@/core/theme';
import { detectionHistoryRepository, type DetectionHistoryRecord } from '@/data/historyRepository';
import { DISEASE_CLASSES } from '@/domain/disease';
import { useAppStore } from '@/core/store/useAppStore';

export default function HistoryScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const language = useAppStore((state) => state.language);
  const storageError = useAppStore((state) => state.storageError);
  const [records, setRecords] = useState<DetectionHistoryRecord[]>([]);
  const [loadError, setLoadError] = useState(false);
  const load = useCallback(async () => {
    try {
      setRecords(await detectionHistoryRepository.list());
      setLoadError(false);
    } catch {
      setLoadError(true);
    }
  }, []);
  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );
  const clear = () =>
    Alert.alert(t('history.clear'), t('history.clearConfirm'), [
      { text: t('common.cancel'), style: 'cancel' },
      {
        text: t('history.clear'),
        style: 'destructive',
        onPress: async () => {
          try {
            await detectionHistoryRepository.clear();
            await load();
            Alert.alert(t('history.clearDone'));
          } catch {
            setLoadError(true);
          }
        },
      },
    ]);

  return (
    <Screen>
      <ScreenHeader
        title={t('history.title')}
        subtitle={t('history.subtitle')}
        back={false}
        right={
          records.length > 0 ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t('history.clear')}
              onPress={clear}
              style={styles.clear}
            >
              <Ionicons name="trash-outline" size={20} color={colors.danger} />
            </Pressable>
          ) : null
        }
      />
      {loadError || storageError ? (
        <SurfaceCard>
          <AppText style={styles.muted}>{t('errors.storage')}</AppText>
          <Pressable onPress={() => void load()}>
            <AppText style={styles.link}>{t('common.retry')}</AppText>
          </Pressable>
        </SurfaceCard>
      ) : null}
      {records.length === 0 ? (
        <View style={styles.empty}>
          <View style={styles.emptyIcon}>
            <Ionicons name="time-outline" size={36} color={colors.primary} />
          </View>
          <AppText variant="title" style={styles.center}>
            {t('history.emptyTitle')}
          </AppText>
          <AppText style={[styles.muted, styles.center]}>{t('history.emptyBody')}</AppText>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/scanner')}
            style={styles.emptyButton}
          >
            <AppText variant="bodyStrong" style={styles.link}>
              {t('home.scanCta')}
            </AppText>
          </Pressable>
        </View>
      ) : (
        records.map((record) => {
          const disease = DISEASE_CLASSES[record.predictedClassId];
          return (
            <SurfaceCard key={record.id} style={styles.record}>
              <Image source={{ uri: record.imageUri }} style={styles.thumbnail} />
              <View style={styles.recordInfo}>
                <AppText variant="bodyStrong">{t(`disease.${disease.key}`)}</AppText>
                <AppText variant="caption" style={styles.muted}>
                  {new Intl.DateTimeFormat(language === 'bn' ? 'bn-BD' : 'en', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  }).format(new Date(record.createdAt))}
                </AppText>
                <AppText variant="caption" style={styles.muted}>
                  {Math.round(record.confidence * 100)}%
                </AppText>
              </View>
            </SurfaceCard>
          );
        })
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  clear: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.dangerBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  empty: {
    flex: 1,
    minHeight: 390,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
  },
  emptyIcon: {
    width: 76,
    height: 76,
    borderRadius: 26,
    backgroundColor: '#E6EFDF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: { textAlign: 'center' },
  muted: { color: colors.textMuted },
  link: { color: colors.primary },
  emptyButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: '#EAF3DE',
    marginTop: spacing.sm,
  },
  record: { flexDirection: 'row', alignItems: 'center' },
  thumbnail: {
    width: 64,
    height: 64,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceMuted,
  },
  recordInfo: { flex: 1, gap: 2 },
});
