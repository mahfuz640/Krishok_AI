import { Pressable, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { PrimaryButton } from '@/components/PrimaryButton';
import { Screen } from '@/components/Screen';
import { SurfaceCard } from '@/components/SurfaceCard';
import { DISEASE_CLASSES } from '@/domain/disease';
import { colors, radius, spacing } from '@/core/theme';

export default function HomeScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  return (
    <Screen>
      <View style={styles.top}>
        <View>
          <AppText variant="caption" style={styles.greeting}>
            {t('home.greeting')}
          </AppText>
          <AppText variant="title">Krishok AI</AppText>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t('nav.settings')}
          onPress={() => router.push('/(tabs)/settings')}
          style={styles.settings}
        >
          <Ionicons name="settings-outline" color={colors.primary} size={21} />
        </Pressable>
      </View>
      <View style={styles.hero}>
        <View style={styles.heroDecoration}>
          <Ionicons name="leaf" size={94} color="#FFFFFF" />
        </View>
        <View style={styles.heroCopy}>
          <AppText variant="heading" style={styles.heroTitle}>
            {t('home.title')}
          </AppText>
          <AppText style={styles.heroText}>{t('home.subtitle')}</AppText>
        </View>
      </View>
      <Notice title={t('home.scanTitle')} body={t('home.offlineNotice')} />
      <SurfaceCard style={styles.scanCard}>
        <View style={styles.iconBox}>
          <Ionicons name="scan-outline" size={25} color={colors.primary} />
        </View>
        <AppText variant="title">{t('home.scanTitle')}</AppText>
        <AppText style={styles.muted}>{t('home.scanBody')}</AppText>
        <PrimaryButton
          label={t('home.scanCta')}
          icon="camera"
          onPress={() => router.push('/scanner')}
        />
      </SurfaceCard>
      <View style={styles.sectionRow}>
        <AppText variant="title">{t('home.libraryTitle')}</AppText>
        <Pressable accessibilityRole="link" onPress={() => router.push('/disease')}>
          <AppText variant="bodyStrong" style={styles.link}>
            {t('home.libraryCta')}
          </AppText>
        </Pressable>
      </View>
      <SurfaceCard>
        <AppText style={styles.muted}>{t('home.libraryBody')}</AppText>
        <View style={styles.diseaseGrid}>
          {DISEASE_CLASSES.map((disease) => (
            <Pressable
              key={disease.id}
              accessibilityRole="link"
              onPress={() =>
                router.push({ pathname: '/disease/[id]', params: { id: String(disease.id) } })
              }
              style={styles.diseaseChip}
            >
              <View style={styles.smallDot} />
              <AppText variant="caption" numberOfLines={1}>
                {t(`disease.${disease.key}`)}
              </AppText>
            </Pressable>
          ))}
        </View>
      </SurfaceCard>
      <View style={styles.tip}>
        <Ionicons name="sunny-outline" size={20} color={colors.warning} />
        <AppText variant="caption" style={styles.tipText}>
          {t('home.healthyTip')}
        </AppText>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  top: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  greeting: { color: colors.textMuted },
  settings: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  hero: {
    minHeight: 182,
    backgroundColor: colors.primaryDark,
    borderRadius: radius.lg,
    padding: spacing.lg,
    overflow: 'hidden',
    justifyContent: 'center',
  },
  heroCopy: { maxWidth: '80%', gap: spacing.sm },
  heroTitle: { color: '#FFFFFF' },
  heroText: { color: '#D8E9DA' },
  heroDecoration: {
    position: 'absolute',
    right: -14,
    bottom: -13,
    width: 122,
    height: 122,
    borderRadius: 61,
    backgroundColor: '#2B754E',
    alignItems: 'center',
    justifyContent: 'center',
    transform: [{ rotate: '-22deg' }],
  },
  scanCard: { padding: spacing.lg },
  iconBox: {
    width: 48,
    height: 48,
    backgroundColor: '#EAF3DE',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  muted: { color: colors.textMuted },
  sectionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  link: { color: colors.primary, fontSize: 13 },
  diseaseGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: spacing.xs },
  diseaseChip: {
    width: '48%',
    minHeight: 42,
    borderRadius: radius.sm,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 9,
  },
  smallDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#83A75B' },
  tip: { flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.xs },
  tipText: { color: colors.textMuted, flex: 1 },
});
