import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { colors } from '@/core/theme';

export default function TabLayout() {
  const { t } = useTranslation();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: '#87948C',
        tabBarStyle: {
          height: 64,
          paddingTop: 7,
          paddingBottom: 8,
          borderTopColor: colors.border,
          backgroundColor: '#FFFFFF',
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('nav.home'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={String(color)} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: t('nav.history'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="time" color={String(color)} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t('nav.settings'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" color={String(color)} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
