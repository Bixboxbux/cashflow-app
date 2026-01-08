# Assets Directory

This directory contains all the assets for the Hook Timer app.

## Required Assets

### Images
- `images/icon.png` - App icon (1024x1024px)
- `images/splash.png` - Splash screen (1284x2778px for iOS, adjust for Android)
- `images/adaptive-icon.png` - Android adaptive icon (1024x1024px with safe zone)

### Sounds
- `sounds/session-complete.mp3` - Sound played when a focus session completes
- `sounds/break-complete.mp3` - Sound played when a break completes
- `sounds/tick.mp3` - Optional: tick sound for each second (disabled by default)

### Animations (Lottie JSON)
- `animations/confetti.json` - Confetti animation for hook unlock
- `animations/fire-streak.json` - Fire animation for streak display

### Fonts (Optional)
- `fonts/Inter-Variable.ttf` - Inter variable font (download from Google Fonts)

## Notes

- All image files should be PNG format with transparent background where appropriate
- Sounds should be MP3 format, short duration (< 2 seconds)
- Lottie animations can be downloaded from https://lottiefiles.com/
- If custom fonts are not added, the app will use system fonts

## Asset Creation Tips

1. **Icon & Splash**:
   - Use a simple, recognizable design
   - Colors: Use the app's primary color (#6366F1 - Indigo)
   - Symbol: Consider a timer/clock icon combined with a motivational element

2. **Sounds**:
   - Keep them pleasant and non-intrusive
   - Session complete: Uplifting/achievement sound
   - Break complete: Gentle reminder sound

3. **Animations**:
   - Confetti: Celebration animation (2-3 seconds)
   - Fire streak: Looping flame animation for streaks > 3 days
