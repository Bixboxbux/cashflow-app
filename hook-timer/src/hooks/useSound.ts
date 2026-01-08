import { useEffect, useState } from 'react';
import { Audio } from 'expo-av';
import { useSettingsStore } from '../store/useSettingsStore';

/**
 * Hook personnalisé pour gérer les sons
 */
export function useSound() {
  const settings = useSettingsStore((state) => state.settings);
  const [sessionCompleteSound, setSessionCompleteSound] = useState<Audio.Sound | null>(null);
  const [breakCompleteSound, setBreakCompleteSound] = useState<Audio.Sound | null>(null);

  useEffect(() => {
    loadSounds();

    return () => {
      unloadSounds();
    };
  }, []);

  const loadSounds = async () => {
    try {
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
      });

      // Pour l'instant, on utilise les sons système
      // Dans une vraie app, vous chargeriez vos propres fichiers audio
      // const { sound: sessionSound } = await Audio.Sound.createAsync(
      //   require('../../assets/sounds/session-complete.mp3')
      // );
      // setSessionCompleteSound(sessionSound);

      // const { sound: breakSound } = await Audio.Sound.createAsync(
      //   require('../../assets/sounds/break-complete.mp3')
      // );
      // setBreakCompleteSound(breakSound);
    } catch (error) {
      console.error('Error loading sounds:', error);
    }
  };

  const unloadSounds = async () => {
    if (sessionCompleteSound) {
      await sessionCompleteSound.unloadAsync();
    }
    if (breakCompleteSound) {
      await breakCompleteSound.unloadAsync();
    }
  };

  const playSessionComplete = async () => {
    if (!settings.notifications.enabled) {
      return;
    }

    try {
      // Pour l'instant, utiliser le son système
      // Dans une vraie app, utilisez sessionCompleteSound?.replayAsync()
      console.log('Playing session complete sound');
    } catch (error) {
      console.error('Error playing session complete sound:', error);
    }
  };

  const playBreakComplete = async () => {
    if (!settings.notifications.enabled) {
      return;
    }

    try {
      // Pour l'instant, utiliser le son système
      // Dans une vraie app, utilisez breakCompleteSound?.replayAsync()
      console.log('Playing break complete sound');
    } catch (error) {
      console.error('Error playing break complete sound:', error);
    }
  };

  const playTick = async () => {
    // Optionnel : son de tick pour chaque seconde
    // Généralement désactivé par défaut pour ne pas être intrusif
  };

  return {
    playSessionComplete,
    playBreakComplete,
    playTick,
  };
}
