/**
 * Formate un nombre de secondes en format MM:SS
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Formate une durée en heures et minutes (ex: "2h 15min")
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours === 0) {
    return `${minutes}min`;
  }

  if (minutes === 0) {
    return `${hours}h`;
  }

  return `${hours}h ${minutes}min`;
}

/**
 * Convertit des minutes en secondes
 */
export function minutesToSeconds(minutes: number): number {
  return minutes * 60;
}

/**
 * Convertit des secondes en minutes
 */
export function secondsToMinutes(seconds: number): number {
  return Math.floor(seconds / 60);
}
