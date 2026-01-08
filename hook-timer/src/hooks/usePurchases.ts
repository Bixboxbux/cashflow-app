import { useEffect, useState } from 'react';
import {
  connectAsync,
  disconnectAsync,
  getProductsAsync,
  purchaseItemAsync,
  finishTransactionAsync,
  getPurchaseHistoryAsync,
  IAPResponseCode,
  InAppPurchase,
} from 'expo-in-app-purchases';
import { usePremiumStore } from '../store/usePremiumStore';
import { PREMIUM_PRODUCT_ID } from '../utils/constants';

/**
 * Hook personnalisé pour gérer les achats in-app
 */
export function usePurchases() {
  const [isLoading, setIsLoading] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  const premiumStore = usePremiumStore();

  useEffect(() => {
    initializePurchases();

    return () => {
      disconnectAsync();
    };
  }, []);

  const initializePurchases = async () => {
    try {
      await connectAsync();
      await loadProducts();
      await restorePurchases();
    } catch (error) {
      console.error('Error initializing purchases:', error);
    }
  };

  const loadProducts = async () => {
    try {
      const { responseCode, results } = await getProductsAsync([PREMIUM_PRODUCT_ID]);

      if (responseCode === IAPResponseCode.OK) {
        setProducts(results || []);
      }
    } catch (error) {
      console.error('Error loading products:', error);
    }
  };

  const purchasePremium = async (): Promise<boolean> => {
    setIsLoading(true);

    try {
      const { responseCode, results } = await purchaseItemAsync(PREMIUM_PRODUCT_ID);

      if (responseCode === IAPResponseCode.OK && results && results.length > 0) {
        const purchase = results[0];

        // Marquer la transaction comme terminée
        await finishTransactionAsync(purchase, false);

        // Activer le premium
        premiumStore.setPremium(true, new Date());

        setIsLoading(false);
        return true;
      }

      setIsLoading(false);
      return false;
    } catch (error) {
      console.error('Error purchasing premium:', error);
      setIsLoading(false);
      return false;
    }
  };

  const restorePurchases = async (): Promise<boolean> => {
    setIsLoading(true);

    try {
      const { responseCode, results } = await getPurchaseHistoryAsync();

      if (responseCode === IAPResponseCode.OK && results) {
        const premiumPurchase = results.find(
          (purchase: InAppPurchase) => purchase.productId === PREMIUM_PRODUCT_ID
        );

        if (premiumPurchase) {
          premiumStore.setPremium(true, new Date(premiumPurchase.transactionDate));
          setIsLoading(false);
          return true;
        }
      }

      setIsLoading(false);
      return false;
    } catch (error) {
      console.error('Error restoring purchases:', error);
      setIsLoading(false);
      return false;
    }
  };

  const getPremiumPrice = (): string => {
    const product = products.find((p) => p.productId === PREMIUM_PRODUCT_ID);
    return product?.price || '4.99€';
  };

  return {
    isLoading,
    purchasePremium,
    restorePurchases,
    getPremiumPrice,
    isPremium: premiumStore.isPremium,
  };
}
