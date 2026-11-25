import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { DISEASE_CLASSES } from '@/domain/disease';
import { colors, spacing } from '@/core/theme';

export default function DiseaseGuideScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  return (
    <Screen>
      <ScreenHeader title={t('disease.title')} subtitle={t('disease.intro')} />
      {DISEASE_CLASSES.map((disease) => (
        <Pressable
          key={disease.id}
          accessibilityRole="link"
          accessibilityLabel={t(`disease.${disease.key}`)}
          onPress={() =>
            router.push({ pathname: '/disease/[id]', params: { id: String(disease.id) } })
          }
        >
          <SurfaceCard style={styles.card}>
            <View style={styles.icon}>
              <Ionicons
                name={disease.id === 2 ? 'checkmark-circle-outline' : 'leaf-outline'}
                size={21}
                color={colors.primary}
              />
            </View>
            <View style={styles.copy}>
              <AppText variant="bodyStrong">
                {disease.id}. {t(`disease.${disease.key}`)}
              </AppText>
              <AppText variant="caption" numberOfLines={2} style={styles.muted}>
                {t(`disease.${disease.key}Info`)}
              </AppText>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
          </SurfaceCard>
        </Pressable>
      ))}
      <Notice title={t('disease.title')} body={t('disease.notice')} tone="info" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  icon: {
    width: 44,
    height: 44,
    borderRadius: 15,
    backgroundColor: colors.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  copy: { flex: 1, gap: 3 },
  muted: { color: colors.textMuted },
});
