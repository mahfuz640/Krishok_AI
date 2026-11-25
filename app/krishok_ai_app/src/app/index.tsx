import { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, radius, spacing } from '@/core/theme';
import { useAppStore } from '@/core/store/useAppStore';

export default function SplashRoute() {
  const { t } = useTranslation();
  const router = useRouter();
  const hydrated = useAppStore((state) => state.hydrated);
  const onboardingComplete = useAppStore((state) => state.onboardingComplete);

  useEffect(() => {
    if (!hydrated) return;
    const timer = setTimeout(
      () => router.replace(onboardingComplete ? '/(tabs)' : '/onboarding'),
      900,
    );
    return () => clearTimeout(timer);
  }, [hydrated, onboardingComplete, router]);

  return (
    <View style={styles.page}>
      <View style={styles.logo}>
        <Ionicons name="leaf" size={42} color={colors.primaryDark} />
      </View>
      <AppText variant="display" style={styles.name}>
        Krishok AI
      </AppText>
      <AppText style={styles.tagline}>{t('splash.tagline')}</AppText>
      <View style={styles.bottom}>
        <PrimaryButton
          label={t('splash.start')}
          icon="arrow-forward"
          onPress={() => router.replace(onboardingComplete ? '/(tabs)' : '/onboarding')}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  logo: {
    width: 88,
    height: 88,
    borderRadius: 30,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  name: { color: colors.primaryDark, letterSpacing: -1 },
  tagline: { color: colors.textMuted, textAlign: 'center', maxWidth: 280, marginTop: spacing.sm },
  bottom: {
    position: 'absolute',
    left: spacing.xl,
    right: spacing.xl,
    bottom: spacing.xl,
    borderRadius: radius.pill,
  },
});
