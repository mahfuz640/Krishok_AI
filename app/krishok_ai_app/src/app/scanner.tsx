import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { PrimaryButton } from '@/components/PrimaryButton';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { useAppStore } from '@/core/store/useAppStore';
import { colors, radius, spacing } from '@/core/theme';

export default function ScannerScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const mode = useAppStore((state) => state.detectionMode);
  const setMode = useAppStore((state) => state.setDetectionMode);
  return (
    <Screen>
      <ScreenHeader title={t('scanner.title')} subtitle={t('scanner.subtitle')} />
      <SurfaceCard>
        <AppText variant="bodyStrong">{t('scanner.mode')}</AppText>
        <View style={styles.modeRow}>
          <ModeChoice
            icon="phone-portrait-outline"
            label={t('scanner.offline')}
            hint={t('scanner.offlineHint')}
            active={mode === 'offline'}
            onPress={() => void setMode('offline')}
          />
          <ModeChoice
            icon="cloud-outline"
            label={t('scanner.online')}
            hint={t('scanner.onlineHint')}
            active={mode === 'online'}
            onPress={() => void setMode('online')}
          />
        </View>
      </SurfaceCard>
      <Notice title={t('scanner.unavailableTitle')} body={t('scanner.unavailableBody')} />
      <PrimaryButton
        label={t('scanner.camera')}
        icon="camera"
        onPress={() => router.push('/camera')}
      />
      <PrimaryButton
        label={t('scanner.gallery')}
        icon="images"
        secondary
        onPress={() => router.push('/gallery')}
      />
      <PrimaryButton
        label={t('scanner.info')}
        icon="book-outline"
        secondary
        onPress={() => router.push('/disease')}
      />
    </Screen>
  );
}

function ModeChoice({
  icon,
  label,
  hint,
  active,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  hint: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.modeChoice, active && styles.modeActive]}>
        <Ionicons name={icon} size={20} color={active ? colors.primary : colors.textMuted} />
        <AppText variant="bodyStrong" style={{ color: active ? colors.primary : colors.text }}>
          {label}
        </AppText>
        <AppText variant="caption" style={styles.hint}>
          {hint}
        </AppText>
        <PrimaryButton
          label={active ? '✓' : label}
          onPress={onPress}
          secondary
          disabled={active}
          accessibilityLabel={label}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  modeRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  modeChoice: {
    minHeight: 155,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.background,
    borderColor: colors.border,
    borderWidth: 1,
    gap: spacing.xs,
  },
  modeActive: { borderColor: colors.primary, backgroundColor: '#F0F7E9' },
  hint: { color: colors.textMuted, flex: 1 },
});
