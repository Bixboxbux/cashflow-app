import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Dimensions,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Button } from '../components/UI/Button';
import { useSettingsStore } from '../store/useSettingsStore';
import { themes } from '../theme/themes';

const { width } = Dimensions.get('window');

const SLIDES = [
  {
    id: '1',
    icon: 'timer-outline' as const,
    title: 'Booste ta productivité',
    description: 'Utilise la technique Pomodoro pour rester concentré et accomplir plus.',
    color: '#6366F1',
  },
  {
    id: '2',
    icon: 'cards-heart' as const,
    title: 'Débloque des hooks inspirants',
    description: 'Chaque session complétée te récompense avec une phrase motivante.',
    color: '#EC4899',
  },
  {
    id: '3',
    icon: 'chart-line' as const,
    title: 'Construis des habitudes',
    description: 'Suis tes progrès et maintiens ton streak pour rester motivé.',
    color: '#10B981',
  },
];

interface OnboardingScreenProps {
  onComplete: () => void;
}

export function OnboardingScreen({ onComplete }: OnboardingScreenProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const handleNext = () => {
    if (currentIndex < SLIDES.length - 1) {
      const nextIndex = currentIndex + 1;
      flatListRef.current?.scrollToIndex({ index: nextIndex });
      setCurrentIndex(nextIndex);
    } else {
      onComplete();
    }
  };

  const handleSkip = () => {
    onComplete();
  };

  const renderSlide = ({ item }: { item: typeof SLIDES[0] }) => (
    <View style={[styles.slide, { width }]}>
      <View
        style={[
          styles.iconContainer,
          { backgroundColor: `${item.color}20` },
        ]}
      >
        <MaterialCommunityIcons
          name={item.icon}
          size={80}
          color={item.color}
        />
      </View>

      <Text
        style={{
          ...theme.typography.h1,
          color: theme.colors.textPrimary,
          textAlign: 'center',
          marginTop: 32,
          marginBottom: 16,
        }}
      >
        {item.title}
      </Text>

      <Text
        style={{
          ...theme.typography.body,
          color: theme.colors.textSecondary,
          textAlign: 'center',
          paddingHorizontal: 32,
        }}
      >
        {item.description}
      </Text>
    </View>
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      {/* Skip button */}
      {currentIndex < SLIDES.length - 1 && (
        <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
          <Text
            style={{
              ...theme.typography.body,
              color: theme.colors.textSecondary,
            }}
          >
            Passer
          </Text>
        </TouchableOpacity>
      )}

      {/* Slides */}
      <FlatList
        ref={flatListRef}
        data={SLIDES}
        renderItem={renderSlide}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(event) => {
          const index = Math.round(event.nativeEvent.contentOffset.x / width);
          setCurrentIndex(index);
        }}
        scrollEnabled={false}
      />

      {/* Pagination dots */}
      <View style={styles.pagination}>
        {SLIDES.map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              {
                backgroundColor:
                  index === currentIndex
                    ? theme.colors.primary
                    : theme.colors.border,
                width: index === currentIndex ? 24 : 8,
              },
            ]}
          />
        ))}
      </View>

      {/* Next/Start button */}
      <View style={styles.buttonContainer}>
        <Button
          title={currentIndex === SLIDES.length - 1 ? 'Commencer' : 'Suivant'}
          onPress={handleNext}
          variant="primary"
          size="large"
          style={styles.button}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  skipButton: {
    position: 'absolute',
    top: 50,
    right: 16,
    zIndex: 10,
    padding: 8,
  },
  slide: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginBottom: 32,
  },
  dot: {
    height: 8,
    borderRadius: 4,
  },
  buttonContainer: {
    paddingHorizontal: 32,
    paddingBottom: 32,
  },
  button: {
    width: '100%',
  },
});
