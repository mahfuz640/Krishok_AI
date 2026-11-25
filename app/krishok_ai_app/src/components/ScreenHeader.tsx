import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from './AppText';
import { colors, spacing } from '@/core/theme';

export function ScreenHeader({
  title,
  subtitle,
  back = true,
  right,
}: {
  title: string;
  subtitle?: string;
  back?: boolean;
  right?: ReactNode;
}) {
  const router = useRouter();
  const { t } = useTranslation();
  return (
    <View style={styles.row}>
      {back ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t('common.back')}
          onPress={() => router.back()}
          style={styles.back}
        >
          <Ionicons name="arrow-back" size={21} color={colors.text} />
        </Pressable>
      ) : null}
      <View style={styles.text}>
        <AppText variant="heading">{title}</AppText>
        {subtitle ? <AppText style={styles.subtitle}>{subtitle}</AppText> : null}
      </View>
      {right}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  back: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 21,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginTop: 2,
  },
  text: { flex: 1, gap: 2 },
  subtitle: { color: colors.textMuted },
});
