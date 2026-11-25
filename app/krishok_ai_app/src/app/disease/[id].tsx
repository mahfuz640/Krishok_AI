import { useLocalSearchParams } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { DISEASE_CLASSES, isDiseaseClassId } from '@/domain/disease';
import { colors, radius, spacing } from '@/core/theme';

export default function DiseaseDetailsScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const diseaseId = Number(id);
  if (!isDiseaseClassId(diseaseId))
    return (
      <Screen>
        <ScreenHeader title={t('errors.generic')} />
        <Notice title={t('errors.generic')} body={t('disease.notice')} tone="error" />
      </Screen>
    );
  const disease = DISEASE_CLASSES[diseaseId];
  return (
    <Screen>
      <ScreenHeader title={t('disease.title')} />
      <View style={styles.hero}>
        <Ionicons
          name={diseaseId === 2 ? 'checkmark-circle' : 'leaf'}
          size={44}
          color={colors.primary}
        />
        <AppText variant="caption" style={styles.eyebrow}>
          {t('disease.classLabel', { id: disease.id })}
        </AppText>
        <AppText variant="display" style={styles.title}>
          {t(`disease.${disease.key}`)}
        </AppText>
      </View>
      <SurfaceCard>
        <AppText variant="title">{t(`disease.${disease.key}`)}</AppText>
        <AppText>{t(`disease.${disease.key}Info`)}</AppText>
      </SurfaceCard>
      <Notice title={t('disease.title')} body={t('disease.notice')} tone="info" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    minHeight: 220,
    borderRadius: radius.lg,
    backgroundColor: '#E5EFD9',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    padding: spacing.lg,
  },
  eyebrow: { color: colors.primary, fontWeight: '700', letterSpacing: 1.1 },
  title: { color: colors.primaryDark, textAlign: 'center' },
});
