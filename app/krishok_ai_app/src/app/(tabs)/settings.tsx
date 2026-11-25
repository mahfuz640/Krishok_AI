import { Pressable, StyleSheet, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { colors, radius, spacing } from '@/core/theme';
import { useAppStore } from '@/core/store/useAppStore';

export default function SettingsScreen() {
  const { t } = useTranslation();
  const language = useAppStore((state) => state.language);
  const mode = useAppStore((state) => state.detectionMode);
  const setLanguage = useAppStore((state) => state.setLanguage);
  const setDetectionMode = useAppStore((state) => state.setDetectionMode);
  const storageError = useAppStore((state) => state.storageError);
  return (
    <Screen>
      <ScreenHeader title={t('settings.title')} subtitle={t('settings.subtitle')} back={false} />
      {storageError ? (
        <Notice title={t('errors.storage')} body={t('settings.storageBody')} tone="error" />
      ) : null}
      <SurfaceCard>
        <AppText variant="title">{t('settings.language')}</AppText>
        <View style={styles.choices}>
          <Choice
            label={t('settings.bangla')}
            selected={language === 'bn'}
            onPress={() => void setLanguage('bn')}
          />
          <Choice
            label={t('settings.english')}
            selected={language === 'en'}
            onPress={() => void setLanguage('en')}
          />
        </View>
      </SurfaceCard>
      <SurfaceCard>
        <AppText variant="title">{t('settings.mode')}</AppText>
        <Choice
          label={t('settings.offline')}
          selected={mode === 'offline'}
          onPress={() => void setDetectionMode('offline')}
          icon="phone-portrait-outline"
        />
        <Choice
          label={t('settings.online')}
          selected={mode === 'online'}
          onPress={() => void setDetectionMode('online')}
          icon="cloud-outline"
        />
      </SurfaceCard>
      <SurfaceCard style={styles.modelCard}>
        <View style={styles.modelRow}>
          <View style={styles.modelIcon}>
            <Ionicons name="sparkles-outline" size={22} color={colors.primary} />
          </View>
          <View style={styles.modelInfo}>
            <AppText variant="bodyStrong">{t('settings.modelName')}</AppText>
            <AppText variant="caption" style={styles.muted}>
              {t('settings.modelStatus')}
            </AppText>
          </View>
        </View>
      </SurfaceCard>
      <SurfaceCard>
        <AppText variant="title">{t('settings.storage')}</AppText>
        <AppText style={styles.muted}>{t('settings.storageBody')}</AppText>
      </SurfaceCard>
      <SurfaceCard>
        <AppText variant="title">{t('settings.about')}</AppText>
        <AppText style={styles.muted}>{t('settings.version')}</AppText>
      </SurfaceCard>
    </Screen>
  );
}

function Choice({
  label,
  selected,
  onPress,
  icon,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      onPress={onPress}
      style={[styles.choice, selected && styles.selected]}
    >
      {icon ? (
        <Ionicons name={icon} color={selected ? colors.primary : colors.textMuted} size={19} />
      ) : null}
      <AppText
        variant="bodyStrong"
        style={{ flex: 1, color: selected ? colors.primary : colors.text }}
      >
        {label}
      </AppText>
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected ? <View style={styles.radioDot} /> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  choices: { flexDirection: 'row', gap: spacing.sm },
  choice: {
    minHeight: 50,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  selected: { borderColor: colors.primary, backgroundColor: '#F0F7E9' },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: { borderColor: colors.primary },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.primary },
  modelCard: { paddingVertical: spacing.md },
  modelRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  modelIcon: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: colors.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modelInfo: { flex: 1, gap: 3 },
  muted: { color: colors.textMuted },
});
