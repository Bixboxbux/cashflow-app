import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Modal } from '../UI/Modal';
import { Button } from '../UI/Button';
import { FeatureComparison } from './FeatureComparison';
import { useSettingsStore } from '../../store/useSettingsStore';
import { usePurchases } from '../../hooks/usePurchases';
import { themes } from '../../theme/themes';

interface PaywallModalProps {
  visible: boolean;
  onClose: () => void;
}

const PREMIUM_FEATURES = [
  {
    icon: 'cards-heart' as const,
    title: '450 hooks premium',
    description: 'Accédez à 500 hooks au total',
  },
  {
    icon: 'chart-line' as const,
    title: 'Statistiques avancées',
    description: 'Heatmap annuelle et graphiques mensuels',
  },
  {
    icon: 'palette' as const,
    title: '5 thèmes de couleur',
    description: 'Personnalisez l\'apparence de votre app',
  },
  {
    icon: 'widgets' as const,
    title: 'Widget Android',
    description: 'Suivez votre timer depuis l\'écran d\'accueil',
  },
  {
    icon: 'shield-check' as const,
    title: 'Badge Supporter',
    description: 'Soutenez le développement de l\'app',
  },
];

export function PaywallModal({ visible, onClose }: PaywallModalProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const { purchasePremium, restorePurchases, getPremiumPrice, isLoading } = usePurchases();

  const handlePurchase = async () => {
    const success = await purchasePremium();
    if (success) {
      onClose();
    }
  };

  const handleRestore = async () => {
    const success = await restorePurchases();
    if (success) {
      onClose();
    }
  };

  return (
    <Modal visible={visible} onClose={onClose} size="large">
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <MaterialCommunityIcons
            name="crown"
            size={48}
            color={theme.colors.warning}
          />

          <Text
            style={{
              ...theme.typography.h1,
              color: theme.colors.textPrimary,
              marginTop: theme.spacing.md,
              textAlign: 'center',
            }}
          >
            Débloquer tout le potentiel
          </Text>

          <Text
            style={{
              ...theme.typography.body,
              color: theme.colors.textSecondary,
              marginTop: theme.spacing.sm,
              textAlign: 'center',
            }}
          >
            Un seul paiement. Aucun abonnement.
          </Text>
        </View>

        {/* Features */}
        <View style={styles.featuresContainer}>
          {PREMIUM_FEATURES.map((feature, index) => (
            <View key={index} style={styles.featureRow}>
              <View
                style={[
                  styles.featureIcon,
                  { backgroundColor: `${theme.colors.primary}20` },
                ]}
              >
                <MaterialCommunityIcons
                  name={feature.icon}
                  size={24}
                  color={theme.colors.primary}
                />
              </View>

              <View style={styles.featureText}>
                <Text
                  style={{
                    ...theme.typography.bodyBold,
                    color: theme.colors.textPrimary,
                  }}
                >
                  {feature.title}
                </Text>
                <Text
                  style={{
                    ...theme.typography.caption,
                    color: theme.colors.textSecondary,
                  }}
                >
                  {feature.description}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Feature Comparison */}
        <FeatureComparison />

        {/* Price */}
        <View style={styles.priceContainer}>
          <Text
            style={{
              ...theme.typography.h1,
              color: theme.colors.primary,
            }}
          >
            {getPremiumPrice()}
          </Text>
          <Text
            style={{
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
            }}
          >
            Paiement unique
          </Text>
        </View>

        {/* Purchase button */}
        <Button
          title={`Acheter - ${getPremiumPrice()}`}
          onPress={handlePurchase}
          variant="primary"
          size="large"
          loading={isLoading}
          style={styles.purchaseButton}
        />

        {/* Restore button */}
        <Button
          title="Restaurer mon achat"
          onPress={handleRestore}
          variant="ghost"
          size="medium"
          loading={isLoading}
        />

        {/* Legal text */}
        <Text
          style={{
            ...theme.typography.small,
            color: theme.colors.textTertiary,
            textAlign: 'center',
            marginTop: theme.spacing.md,
          }}
        >
          Paiement unique. Pas d'abonnement. L'achat sera débité sur votre
          compte Google Play.
        </Text>
      </ScrollView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  featuresContainer: {
    marginVertical: 16,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  featureText: {
    flex: 1,
  },
  priceContainer: {
    alignItems: 'center',
    marginVertical: 24,
  },
  purchaseButton: {
    marginBottom: 12,
  },
});
