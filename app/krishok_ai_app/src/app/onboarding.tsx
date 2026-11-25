import { Pressable, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { PrimaryButton } from '@/components/PrimaryButton';
import { Screen } from '@/components/Screen';
import { colors, radius, spacing } from '@/core/theme';
import { useAppStore } from '@/core/store/useAppStore';

export default function OnboardingScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const language = useAppStore((state) => state.language);
  const setLanguage = useAppStore((state) => state.setLanguage);
  const finishOnboarding = useAppStore((state) => state.finishOnboarding);
  const choose = async (value: 'en' | 'bn') => {
    await setLanguage(value);
  };
  const finish = async () => {
    await finishOnboarding();
    router.replace('/(tabs)');
  };

  return (
    <Screen contentStyle={styles.page}>
      <View style={styles.art}>
        <View style={styles.sun} />
        <Ionicons name="leaf" size={70} color={colors.primary} />
        <View style={styles.ground} />
      </View>
      <AppText variant="caption" style={styles.eyebrow}>
        {t('onboarding.eyebrow')}
      </AppText>
      <AppText variant="display" style={styles.title}>
        {t('onboarding.title')}
      </AppText>
      <AppText style={styles.body}>{t('onboarding.body')}</AppText>
      <View style={styles.languageBlock}>
        <AppText variant="bodyStrong">{t('onboarding.chooseLanguage')}</AppText>
        <View style={styles.languages}>
          <LanguageOption
            label="বাংলা"
            active={language === 'bn'}
            onPress={() => void choose('bn')}
          />
          <LanguageOption
            label="English"
            active={language === 'en'}
            onPress={() => void choose('en')}
          />
        </View>
        <AppText variant="caption" style={styles.hint}>
          {t('onboarding.languageHint')}
        </AppText>
      </View>
      <PrimaryButton
        label={t('common.continue')}
        icon="arrow-forward"
        onPress={() => void finish()}
      />
    </Screen>
  );
}

function LanguageOption({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: active }}
      onPress={onPress}
      style={[styles.languageOption, active && styles.languageActive]}
    >
      <AppText variant="bodyStrong" style={{ color: active ? colors.primary : colors.text }}>
        {label}
      </AppText>
      {active ? <Ionicons name="checkmark-circle" size={20} color={colors.primary} /> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1, justifyContent: 'center', paddingTop: spacing.xl },
  art: {
    height: 170,
    borderRadius: radius.lg,
    backgroundColor: '#E7F0DE',
    marginBottom: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  sun: {
    position: 'absolute',
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: colors.accent,
    right: 44,
    top: 24,
  },
  ground: {
    position: 'absolute',
    width: '120%',
    height: 58,
    borderTopLeftRadius: 60,
    borderTopRightRadius: 60,
    bottom: -29,
    backgroundColor: '#B8D89B',
  },
  eyebrow: { color: colors.primary, fontWeight: '700', letterSpacing: 1.2 },
  title: { color: colors.primaryDark, marginTop: spacing.xs },
  body: { color: colors.textMuted, marginTop: spacing.sm },
  languageBlock: { marginTop: spacing.xl, gap: spacing.sm },
  languages: { flexDirection: 'row', gap: spacing.sm },
  languageOption: {
    flex: 1,
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  languageActive: { borderColor: colors.primary, backgroundColor: '#F0F7E9' },
  hint: { color: colors.textMuted, marginBottom: spacing.sm },
});
