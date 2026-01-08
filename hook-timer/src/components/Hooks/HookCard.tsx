import React from 'react';
import { View, Text, StyleSheet, Share } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { Hook } from '../../types/hook';
import { Card } from '../UI/Card';
import { Badge } from '../UI/Badge';
import { IconButton } from '../UI/IconButton';
import { useSettingsStore } from '../../store/useSettingsStore';
import { useHooksStore } from '../../store/useHooksStore';
import { themes } from '../../theme/themes';

interface HookCardProps {
  hook: Hook;
}

export function HookCard({ hook }: HookCardProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const toggleFavorite = useHooksStore((state) => state.toggleFavorite);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `"${hook.text}" - Hook Timer`,
      });
    } catch (error) {
      console.error('Error sharing hook:', error);
    }
  };

  const handleToggleFavorite = () => {
    toggleFavorite(hook.id);
  };

  const categoryColor = theme.categoryColors[hook.category];

  return (
    <Card elevated style={styles.card}>
      <View style={styles.header}>
        <Badge
          text={hook.category.toUpperCase()}
          color={categoryColor}
          textColor="#FFFFFF"
        />

        <View style={styles.actions}>
          <IconButton
            icon={hook.isFavorite ? 'heart' : 'heart-outline'}
            onPress={handleToggleFavorite}
            size={20}
            color={hook.isFavorite ? theme.colors.error : theme.colors.textSecondary}
          />
          <IconButton
            icon="share-variant"
            onPress={handleShare}
            size={20}
            color={theme.colors.textSecondary}
          />
        </View>
      </View>

      <Text
        style={{
          ...theme.typography.body,
          color: theme.colors.textPrimary,
          marginVertical: theme.spacing.md,
        }}
      >
        {hook.text}
      </Text>

      {hook.unlockedAt && (
        <Text
          style={{
            ...theme.typography.small,
            color: theme.colors.textTertiary,
          }}
        >
          Débloqué le {format(new Date(hook.unlockedAt), 'dd/MM/yyyy')}
        </Text>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
});
