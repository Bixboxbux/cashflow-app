import { TextStyle } from 'react-native';

export const typography: Record<string, TextStyle> = {
  h1: {
    fontSize: 32,
    fontWeight: '700',
    lineHeight: 40
  },
  h2: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32
  },
  h3: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24
  },
  bodyBold: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 24
  },
  caption: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20
  },
  small: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16
  },
  timer: {
    fontSize: 72,
    fontWeight: '700',
    lineHeight: 80,
    fontVariant: ['tabular-nums']
  },
};
