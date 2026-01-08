export const darkTheme = {
  background: '#0D0D0F',
  surface: '#1A1A1F',
  surfaceElevated: '#252529',
  primary: '#6366F1', // Indigo
  primaryLight: '#818CF8',
  secondary: '#22D3EE', // Cyan
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  textPrimary: '#FFFFFF',
  textSecondary: '#A1A1AA',
  textTertiary: '#71717A',
  border: '#27272A',
};

export const lightTheme = {
  background: '#FAFAFA',
  surface: '#FFFFFF',
  surfaceElevated: '#F4F4F5',
  primary: '#4F46E5',
  primaryLight: '#6366F1',
  secondary: '#0891B2',
  success: '#059669',
  warning: '#D97706',
  error: '#DC2626',
  textPrimary: '#18181B',
  textSecondary: '#52525B',
  textTertiary: '#A1A1AA',
  border: '#E4E4E7',
};

export const categoryColors = {
  motivation: '#F59E0B', // Amber
  productivity: '#10B981', // Emerald
  mindset: '#8B5CF6', // Violet
  success: '#EC4899', // Pink
  discipline: '#3B82F6', // Blue
};

export type Theme = typeof darkTheme;
export type CategoryColor = keyof typeof categoryColors;
