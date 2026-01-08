import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TextInput,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { HookCard } from './HookCard';
import { useHooksStore } from '../../store/useHooksStore';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';
import { HookFilter } from '../../types/hook';

const FILTERS: { label: string; value: HookFilter }[] = [
  { label: 'Tous', value: 'all' },
  { label: 'Favoris', value: 'favorites' },
  { label: 'Motivation', value: 'motivation' },
  { label: 'Productivité', value: 'productivity' },
  { label: 'Mindset', value: 'mindset' },
  { label: 'Succès', value: 'success' },
  { label: 'Discipline', value: 'discipline' },
];

export function HookList() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const getFilteredHooks = useHooksStore((state) => state.getFilteredHooks);
  const getUnlockedCount = useHooksStore((state) => state.getUnlockedCount);
  const getTotalCount = useHooksStore((state) => state.getTotalCount);

  const [selectedFilter, setSelectedFilter] = useState<HookFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const hooks = getFilteredHooks(selectedFilter).filter((hook) =>
    hook.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const unlockedCount = getUnlockedCount();
  const totalCount = getTotalCount();

  return (
    <View style={styles.container}>
      {/* Header with progress */}
      <View style={styles.header}>
        <Text
          style={{
            ...theme.typography.h2,
            color: theme.colors.textPrimary,
          }}
        >
          {unlockedCount}/{totalCount} hooks
        </Text>

        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              {
                width: `${(unlockedCount / totalCount) * 100}%`,
                backgroundColor: theme.colors.primary,
              },
            ]}
          />
        </View>
      </View>

      {/* Search bar */}
      <View
        style={[
          styles.searchContainer,
          {
            backgroundColor: theme.colors.surface,
            borderColor: theme.colors.border,
          },
        ]}
      >
        <MaterialCommunityIcons
          name="magnify"
          size={20}
          color={theme.colors.textSecondary}
        />
        <TextInput
          style={[
            styles.searchInput,
            {
              ...theme.typography.body,
              color: theme.colors.textPrimary,
            },
          ]}
          placeholder="Rechercher..."
          placeholderTextColor={theme.colors.textTertiary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Filters */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        {FILTERS.map((filter) => (
          <TouchableOpacity
            key={filter.value}
            style={[
              styles.filterChip,
              {
                backgroundColor:
                  selectedFilter === filter.value
                    ? theme.colors.primary
                    : theme.colors.surface,
                borderColor: theme.colors.border,
              },
            ]}
            onPress={() => setSelectedFilter(filter.value)}
          >
            <Text
              style={{
                ...theme.typography.caption,
                color:
                  selectedFilter === filter.value
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
                fontWeight: selectedFilter === filter.value ? '600' : '400',
              }}
            >
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Hooks list */}
      <FlatList
        data={hooks}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <HookCard hook={item} />}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <MaterialCommunityIcons
              name="emoticon-sad-outline"
              size={64}
              color={theme.colors.textTertiary}
            />
            <Text
              style={{
                ...theme.typography.body,
                color: theme.colors.textSecondary,
                marginTop: theme.spacing.md,
                textAlign: 'center',
              }}
            >
              Aucun hook trouvé
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E4E4E7',
    borderRadius: 4,
    marginTop: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
  },
  filtersContainer: {
    maxHeight: 50,
    marginBottom: 8,
  },
  filtersContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  listContent: {
    padding: 16,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
});
