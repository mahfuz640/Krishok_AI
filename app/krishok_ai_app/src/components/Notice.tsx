import { StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from './AppText';
import { colors, radius, spacing } from '@/core/theme';

export function Notice({
  title,
  body,
  tone = 'warning',
}: {
  title: string;
  body: string;
  tone?: 'warning' | 'error' | 'info';
}) {
  const palette =
    tone === 'error'
      ? { bg: colors.dangerBg, fg: colors.danger, icon: 'alert-circle' as const }
      : tone === 'info'
        ? { bg: colors.surfaceMuted, fg: colors.primary, icon: 'information-circle' as const }
        : { bg: colors.warningBg, fg: colors.warning, icon: 'leaf' as const };
  return (
    <View accessibilityRole="summary" style={[styles.container, { backgroundColor: palette.bg }]}>
      <Ionicons name={palette.icon} size={20} color={palette.fg} />
      <View style={styles.copy}>
        <AppText variant="bodyStrong" style={{ color: palette.fg }}>
          {title}
        </AppText>
        <AppText variant="caption" style={{ color: palette.fg }}>
          {body}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  copy: { flex: 1, gap: 3 },
});
