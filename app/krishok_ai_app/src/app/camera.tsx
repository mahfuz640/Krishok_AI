import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Linking, Pressable, StyleSheet, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { AppText } from '@/components/AppText';
import { Notice } from '@/components/Notice';
import { Screen } from '@/components/Screen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { PrimaryButton } from '@/components/PrimaryButton';
import { SurfaceCard } from '@/components/SurfaceCard';
import { detectDisease } from '@/core/ai/detectionService';
import { DetectionServiceError } from '@/core/ai/errors';
import { colors, radius, spacing } from '@/core/theme';
import { DISEASE_CLASSES, type PredictionResult } from '@/domain/disease';

export default function CameraScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const camera = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<'back' | 'front'>('back');
  const [ready, setReady] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState('');
  const [live, setLive] = useState(false);
  const [liveBusy, setLiveBusy] = useState(false);
  const [livePrediction, setLivePrediction] = useState<PredictionResult | null>(null);
  const [liveError, setLiveError] = useState('');
  const liveActive = useRef(false);
  const mounted = useRef(true);

  useEffect(
    () => {
      mounted.current = true;
      return () => {
        mounted.current = false;
        liveActive.current = false;
      };
    },
    [],
  );

  const capture = async () => {
    if (!camera.current || !ready || capturing || liveActive.current) return;
    setError('');
    setCapturing(true);
    try {
      const photo = await camera.current.takePictureAsync({
        quality: 0.92,
        exif: false,
        shutterSound: true,
      });
      if (!photo?.uri) throw new Error('MissingPhotoUri');
      router.replace({ pathname: '/result', params: { imageUri: photo.uri } });
    } catch {
      setError(t('camera.error'));
    } finally {
      setCapturing(false);
    }
  };

  const toggleLiveDetection = async () => {
    if (liveActive.current) {
      liveActive.current = false;
      setLive(false);
      return;
    }
    if (!camera.current || !ready) return;

    liveActive.current = true;
    setLive(true);
    setLiveError('');
    setLivePrediction(null);

    while (liveActive.current) {
      setLiveBusy(true);
      try {
        const photo = await camera.current?.takePictureAsync({
          quality: 0.48,
          exif: false,
          shutterSound: false,
        });
        if (!photo?.uri) throw new Error('MissingLiveFrame');
        const prediction = await detectDisease({ imageUri: photo.uri, mode: 'online' });
        if (liveActive.current && mounted.current) setLivePrediction(prediction);
      } catch (cause) {
        if (liveActive.current && mounted.current) {
          setLiveError(
            cause instanceof DetectionServiceError && cause.code === 'ONLINE_NOT_CONFIGURED'
              ? t('errors.onlineNotConfigured')
              : t('camera.liveError'),
          );
        }
        liveActive.current = false;
      } finally {
        if (mounted.current) setLiveBusy(false);
      }
      if (liveActive.current) {
        await new Promise((resolve) => setTimeout(resolve, 1400));
      }
    }
    if (mounted.current) setLive(false);
  };

  const selectedDisease = livePrediction ? DISEASE_CLASSES[livePrediction.classId] : null;

  return (
    <Screen>
      <ScreenHeader title={t('camera.title')} />
      {!permission ? (
        <View style={styles.permission}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : !permission.granted ? (
        <View style={styles.permission}>
          <View style={styles.permissionIcon}>
            <Ionicons name="camera-outline" size={30} color={colors.primary} />
          </View>
          <AppText variant="title" style={styles.center}>
            {t('camera.permissionTitle')}
          </AppText>
          <AppText style={[styles.muted, styles.center]}>
            {permission.canAskAgain ? t('camera.permissionBody') : t('camera.denied')}
          </AppText>
          <PrimaryButton
            label={permission.canAskAgain ? t('camera.grant') : t('common.retry')}
            icon="camera"
            onPress={() =>
              permission.canAskAgain ? void requestPermission() : void Linking.openSettings()
            }
          />
        </View>
      ) : (
        <>
          <View style={styles.previewWrap}>
            <CameraView
              ref={camera}
              style={styles.preview}
              facing={facing}
              onCameraReady={() => setReady(true)}
              onMountError={() => setError(t('camera.unavailable'))}
            />
            <View pointerEvents="none" style={styles.frame}>
              <View style={styles.cornerTL} />
              <View style={styles.cornerTR} />
              <View style={styles.cornerBL} />
              <View style={styles.cornerBR} />
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t('camera.flip')}
              onPress={() => setFacing((current) => (current === 'back' ? 'front' : 'back'))}
              style={styles.flip}
              disabled={live}
            >
              <Ionicons name="sync" size={22} color="#FFFFFF" />
            </Pressable>
          </View>
          {error ? <Notice title={t('errors.generic')} body={error} tone="error" /> : null}
          <AppText variant="caption" style={styles.muted}>
            {t('home.healthyTip')}
          </AppText>
          <PrimaryButton
            label={live ? t('camera.liveStop') : t('camera.liveStart')}
            icon={live ? 'pause' : 'scan'}
            secondary={!live}
            onPress={() => void toggleLiveDetection()}
            disabled={!ready || capturing}
          />
          <AppText variant="caption" style={styles.muted}>
            {t('camera.livePrivacy')}
          </AppText>
          {live || liveBusy ? (
            <SurfaceCard style={styles.liveStatus}>
              <View style={styles.liveDot} />
              <AppText style={styles.liveStatusText}>
                {liveBusy ? t('camera.liveAnalyzing') : t('camera.liveActive')}
              </AppText>
            </SurfaceCard>
          ) : null}
          {liveError ? (
            <Notice title={t('errors.generic')} body={liveError} tone="error" />
          ) : null}
          {selectedDisease && livePrediction ? (
            <SurfaceCard style={styles.liveResult}>
              <AppText variant="caption" style={styles.muted}>
                {t('camera.liveResult')}
              </AppText>
              <AppText variant="title">{t(`disease.${selectedDisease.key}`)}</AppText>
              <AppText style={styles.muted}>
                {t('camera.confidence', { value: Math.round(livePrediction.confidence * 100) })}
              </AppText>
            </SurfaceCard>
          ) : null}
          <PrimaryButton
            label={t('camera.capture')}
            icon="camera"
            onPress={() => void capture()}
            loading={capturing}
            disabled={!ready || live || capturing}
          />
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  permission: { flex: 1, minHeight: 400, justifyContent: 'center', gap: spacing.md },
  permissionIcon: {
    alignSelf: 'center',
    width: 66,
    height: 66,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E6EFDF',
  },
  center: { textAlign: 'center' },
  muted: { color: colors.textMuted },
  liveStatus: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm },
  liveStatusText: { color: colors.primaryDark },
  liveDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: '#D64E43' },
  liveResult: { gap: spacing.xs },
  previewWrap: {
    height: 470,
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: '#17251C',
  },
  preview: { flex: 1 },
  frame: { ...StyleSheet.absoluteFill, margin: 34 },
  cornerTL: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: 36,
    height: 36,
    borderLeftWidth: 3,
    borderTopWidth: 3,
    borderColor: '#FFFFFF',
    borderTopLeftRadius: 12,
  },
  cornerTR: {
    position: 'absolute',
    right: 0,
    top: 0,
    width: 36,
    height: 36,
    borderRightWidth: 3,
    borderTopWidth: 3,
    borderColor: '#FFFFFF',
    borderTopRightRadius: 12,
  },
  cornerBL: {
    position: 'absolute',
    left: 0,
    bottom: 0,
    width: 36,
    height: 36,
    borderLeftWidth: 3,
    borderBottomWidth: 3,
    borderColor: '#FFFFFF',
    borderBottomLeftRadius: 12,
  },
  cornerBR: {
    position: 'absolute',
    right: 0,
    bottom: 0,
    width: 36,
    height: 36,
    borderRightWidth: 3,
    borderBottomWidth: 3,
    borderColor: '#FFFFFF',
    borderBottomRightRadius: 12,
  },
  flip: {
    position: 'absolute',
    right: 18,
    top: 18,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#173B2DCC',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
