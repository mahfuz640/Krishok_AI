import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from './AppText';
import { colors, radius, spacing } from '@/core/theme';

type Props = {
  label: string;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
  secondary?: boolean;
  disabled?: boolean;
  loading?: boolean;
  accessibilityLabel?: string;
};

export function PrimaryButton({
  label,
  onPress,
  icon,
  secondary = false,
  disabled = false,
  loading = false,
  accessibilityLabel,
}: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondary,
        (disabled || loading) && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={secondary ? colors.primary : '#FFFFFF'} />
      ) : (
        <View style={styles.content}>
          {icon ? (
            <Ionicons name={icon} size={20} color={secondary ? colors.primary : '#FFFFFF'} />
          ) : null}
          <AppText variant="bodyStrong" style={{ color: secondary ? colors.primary : '#FFFFFF' }}>
            {label}
          </AppText>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 54,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  secondary: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  disabled: { opacity: 0.55 },
  pressed: { transform: [{ scale: 0.985 }] },
  content: {
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
