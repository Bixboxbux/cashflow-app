export type HookCategory = 'motivation' | 'productivity' | 'mindset' | 'success' | 'discipline';

export interface Hook {
  id: string;
  text: string; // La phrase d'accroche (max 150 caractères)
  category: HookCategory;
  isPremium: boolean;
  unlockedAt?: Date;
  isFavorite: boolean;
}

export type HookFilter = 'all' | 'favorites' | HookCategory;
