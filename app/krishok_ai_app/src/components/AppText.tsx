import { Text as NativeText, type TextProps, type TextStyle } from 'react-native';
import { useAppStore } from '@/core/store/useAppStore';

type Props = TextProps & {
  variant?: 'body' | 'bodyStrong' | 'caption' | 'title' | 'heading' | 'display';
};

const variants: Record<NonNullable<Props['variant']>, TextStyle> = {
  body: { fontSize: 16, lineHeight: 25 },
  bodyStrong: { fontSize: 16, lineHeight: 25, fontWeight: '600' },
  caption: { fontSize: 13, lineHeight: 20 },
  title: { fontSize: 20, lineHeight: 28, fontWeight: '700' },
  heading: { fontSize: 26, lineHeight: 34, fontWeight: '700' },
  display: { fontSize: 34, lineHeight: 42, fontWeight: '700' },
};

export function AppText({ variant = 'body', style, ...props }: Props) {
  const language = useAppStore((state) => state.language);
  const fontWeight = (style as TextStyle | undefined)?.fontWeight ?? variants[variant].fontWeight;
  const fontFamily =
    language === 'bn'
      ? fontWeight === '700'
        ? 'HindSiliguri_700Bold'
        : fontWeight === '600'
          ? 'HindSiliguri_600SemiBold'
          : 'HindSiliguri_400Regular'
      : undefined;
  return (
    <NativeText {...props} style={[variants[variant], { color: '#14271D', fontFamily }, style]} />
  );
}
