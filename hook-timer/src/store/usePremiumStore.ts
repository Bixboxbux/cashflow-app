import { create } from 'zustand';
import { STORAGE_KEYS, PREMIUM_PRODUCT_ID } from '../utils/constants';
import { saveData, loadData } from '../utils/storage';

interface PremiumData {
  isPremium: boolean;
  purchaseDate?: Date;
  productId?: string;
}

interface PremiumStore extends PremiumData {
  // Actions
  setPremium: (isPremium: boolean, purchaseDate?: Date) => void;
  checkPremiumStatus: () => Promise<void>;
  loadPremium: () => Promise<void>;
  savePremium: () => Promise<void>;
}

export const usePremiumStore = create<PremiumStore>((set, get) => ({
  isPremium: false,
  purchaseDate: undefined,
  productId: undefined,

  setPremium: (isPremium, purchaseDate) => {
    set({
      isPremium,
      purchaseDate: purchaseDate || new Date(),
      productId: isPremium ? PREMIUM_PRODUCT_ID : undefined,
    });
    get().savePremium();
  },

  checkPremiumStatus: async () => {
    // Cette fonction sera implémentée avec expo-in-app-purchases
    // Pour vérifier le statut réel de l'achat auprès de Google Play
    await get().loadPremium();
  },

  loadPremium: async () => {
    const data = await loadData<PremiumData>(STORAGE_KEYS.PREMIUM);
    if (data) {
      set(data);
    }
  },

  savePremium: async () => {
    const state = get();
    await saveData(STORAGE_KEYS.PREMIUM, {
      isPremium: state.isPremium,
      purchaseDate: state.purchaseDate,
      productId: state.productId,
    });
  },
}));
