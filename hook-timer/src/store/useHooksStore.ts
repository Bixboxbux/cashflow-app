import { create } from 'zustand';
import { Hook, HookFilter } from '../types/hook';
import { STORAGE_KEYS } from '../utils/constants';
import { saveData, loadData } from '../utils/storage';
import { freeHooks } from '../data/hooks-free';
import { premiumHooks } from '../data/hooks-premium';

interface HooksStore {
  hooks: Hook[];
  unlockedHookIds: Set<string>;
  lastUnlockedHook: Hook | null;

  // Actions
  initializeHooks: () => void;
  unlockRandomHook: () => Hook | null;
  toggleFavorite: (hookId: string) => void;
  getFilteredHooks: (filter: HookFilter) => Hook[];
  getUnlockedCount: () => number;
  getTotalCount: () => number;
  loadHooks: () => Promise<void>;
  saveHooks: () => Promise<void>;
}

export const useHooksStore = create<HooksStore>((set, get) => ({
  hooks: [],
  unlockedHookIds: new Set(),
  lastUnlockedHook: null,

  initializeHooks: () => {
    // Combiner les hooks gratuits et premium
    const allHooks: Hook[] = [
      ...freeHooks.map((h) => ({ ...h, unlockedAt: undefined, isFavorite: false })),
      ...premiumHooks.map((h) => ({ ...h, unlockedAt: undefined, isFavorite: false })),
    ];

    set({ hooks: allHooks });
  },

  unlockRandomHook: () => {
    const state = get();

    // Obtenir les hooks non débloqués
    const lockedHooks = state.hooks.filter(
      (hook) => !state.unlockedHookIds.has(hook.id)
    );

    if (lockedHooks.length === 0) {
      return null;
    }

    // Choisir un hook aléatoire
    const randomIndex = Math.floor(Math.random() * lockedHooks.length);
    const unlockedHook = lockedHooks[randomIndex];

    // Marquer comme débloqué
    const updatedHooks = state.hooks.map((hook) =>
      hook.id === unlockedHook.id
        ? { ...hook, unlockedAt: new Date() }
        : hook
    );

    const newUnlockedIds = new Set(state.unlockedHookIds);
    newUnlockedIds.add(unlockedHook.id);

    set({
      hooks: updatedHooks,
      unlockedHookIds: newUnlockedIds,
      lastUnlockedHook: { ...unlockedHook, unlockedAt: new Date() },
    });

    get().saveHooks();

    return { ...unlockedHook, unlockedAt: new Date() };
  },

  toggleFavorite: (hookId) => {
    const state = get();
    const updatedHooks = state.hooks.map((hook) =>
      hook.id === hookId ? { ...hook, isFavorite: !hook.isFavorite } : hook
    );

    set({ hooks: updatedHooks });
    get().saveHooks();
  },

  getFilteredHooks: (filter) => {
    const state = get();

    let filtered = state.hooks.filter((hook) =>
      state.unlockedHookIds.has(hook.id)
    );

    if (filter === 'all') {
      return filtered;
    }

    if (filter === 'favorites') {
      return filtered.filter((hook) => hook.isFavorite);
    }

    return filtered.filter((hook) => hook.category === filter);
  },

  getUnlockedCount: () => {
    return get().unlockedHookIds.size;
  },

  getTotalCount: () => {
    return get().hooks.length;
  },

  loadHooks: async () => {
    const data = await loadData<{
      hooks: Hook[];
      unlockedHookIds: string[];
    }>(STORAGE_KEYS.HOOKS);

    if (data) {
      set({
        hooks: data.hooks,
        unlockedHookIds: new Set(data.unlockedHookIds),
      });
    } else {
      get().initializeHooks();
    }
  },

  saveHooks: async () => {
    const state = get();
    await saveData(STORAGE_KEYS.HOOKS, {
      hooks: state.hooks,
      unlockedHookIds: Array.from(state.unlockedHookIds),
    });
  },
}));
