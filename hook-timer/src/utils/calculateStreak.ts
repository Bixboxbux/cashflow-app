import { format, subDays, parseISO, isToday, isYesterday } from 'date-fns';
import { DailyStats } from '../types/stats';

/**
 * Calcule le streak actuel basé sur les statistiques quotidiennes
 * Un jour compte pour le streak s'il a au moins 1 session complétée
 */
export function calculateCurrentStreak(dailyStats: Record<string, DailyStats>): number {
  const today = format(new Date(), 'yyyy-MM-dd');
  let streak = 0;
  let currentDate = today;

  // Vérifier si aujourd'hui a des sessions
  if (dailyStats[currentDate]?.sessionsCompleted > 0) {
    streak = 1;
  } else {
    // Si pas de session aujourd'hui, commencer à hier
    currentDate = format(subDays(new Date(), 1), 'yyyy-MM-dd');
    if (!dailyStats[currentDate] || dailyStats[currentDate].sessionsCompleted === 0) {
      return 0;
    }
    streak = 1;
  }

  // Remonter dans le temps jour par jour
  for (let i = 1; i < 365; i++) {
    const checkDate = format(subDays(parseISO(currentDate), i), 'yyyy-MM-dd');

    if (!dailyStats[checkDate] || dailyStats[checkDate].sessionsCompleted === 0) {
      break;
    }

    streak++;
  }

  return streak;
}

/**
 * Calcule le meilleur streak de tous les temps
 */
export function calculateBestStreak(dailyStats: Record<string, DailyStats>): number {
  const sortedDates = Object.keys(dailyStats).sort();

  if (sortedDates.length === 0) {
    return 0;
  }

  let maxStreak = 0;
  let currentStreak = 0;
  let lastDate: Date | null = null;

  for (const dateStr of sortedDates) {
    const stats = dailyStats[dateStr];

    if (stats.sessionsCompleted === 0) {
      currentStreak = 0;
      lastDate = null;
      continue;
    }

    const currentDate = parseISO(dateStr);

    if (!lastDate) {
      currentStreak = 1;
    } else {
      const daysDiff = Math.floor(
        (currentDate.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysDiff === 1) {
        currentStreak++;
      } else {
        currentStreak = 1;
      }
    }

    maxStreak = Math.max(maxStreak, currentStreak);
    lastDate = currentDate;
  }

  return maxStreak;
}

/**
 * Vérifie si une date est éligible pour maintenir le streak
 */
export function isStreakActive(dailyStats: Record<string, DailyStats>): boolean {
  const today = format(new Date(), 'yyyy-MM-dd');
  const yesterday = format(subDays(new Date(), 1), 'yyyy-MM-dd');

  // Le streak est actif si on a des sessions aujourd'hui ou hier
  return (
    (dailyStats[today]?.sessionsCompleted ?? 0) > 0 ||
    (dailyStats[yesterday]?.sessionsCompleted ?? 0) > 0
  );
}
