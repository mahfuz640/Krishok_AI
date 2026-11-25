import type { ReactNode } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { colors, radius, spacing } from '@/core/theme';

export function SurfaceCard({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderColor: colors.border,
    borderWidth: StyleSheet.hairlineWidth,
    gap: spacing.sm,
  },
});
