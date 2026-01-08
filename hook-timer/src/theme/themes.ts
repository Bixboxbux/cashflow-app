import { darkTheme, lightTheme, categoryColors } from './colors';
import { typography } from './typography';
import { spacing, radius } from './spacing';

export const themes = {
  dark: {
    colors: darkTheme,
    categoryColors,
    typography,
    spacing,
    radius,
  },
  light: {
    colors: lightTheme,
    categoryColors,
    typography,
    spacing,
    radius,
  },
};

export type ThemeMode = 'dark' | 'light';
export type AppTheme = typeof themes.dark;
