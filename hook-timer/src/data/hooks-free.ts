import { Hook } from '../types/hook';

/**
 * 50 hooks gratuits répartis par catégorie
 * - 10 par catégorie (motivation, productivity, mindset, success, discipline)
 */
export const freeHooks: Omit<Hook, 'unlockedAt' | 'isFavorite'>[] = [
  // MOTIVATION (10)
  {
    id: '1',
    text: "Le succès n'est pas final, l'échec n'est pas fatal : c'est le courage de continuer qui compte.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '2',
    text: "Tu n'as pas besoin d'être parfait pour commencer, mais tu dois commencer pour devenir meilleur.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '3',
    text: "Chaque expert a d'abord été un débutant. Ne laisse pas la peur de l'échec t'empêcher d'essayer.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '4',
    text: "La motivation te fait démarrer, l'habitude te fait continuer.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '5',
    text: "Commence là où tu es. Utilise ce que tu as. Fais ce que tu peux.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '6',
    text: "Le seul endroit où le succès vient avant le travail, c'est dans le dictionnaire.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '7',
    text: "Crois en toi et tout devient possible.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '8',
    text: "Les opportunités ne se présentent pas, tu les crées.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '9',
    text: "Le secret pour avancer, c'est de commencer.",
    category: 'motivation',
    isPremium: false,
  },
  {
    id: '10',
    text: "Ne regarde pas l'horloge. Fais ce qu'elle fait : continue d'avancer.",
    category: 'motivation',
    isPremium: false,
  },

  // PRODUCTIVITY (10)
  {
    id: '11',
    text: "Chaque minute que tu passes à planifier t'en fait gagner dix à l'exécution.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '12',
    text: "La concentration, c'est l'art d'ignorer ce qui n'est pas important.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '13',
    text: "Fais une chose à la fois et fais-la bien.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '14',
    text: "L'action est la clé fondamentale de tout succès.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '15',
    text: "Mange la grenouille le matin : commence par la tâche la plus difficile.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '16',
    text: "Le temps perdu ne se rattrape jamais. Utilise-le sagement.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '17',
    text: "Moins de distractions = Plus d'accomplissements.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '18',
    text: "La perfection est l'ennemie du fait. Fini vaut mieux que parfait.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '19',
    text: "Travaille intelligemment, pas seulement durement.",
    category: 'productivity',
    isPremium: false,
  },
  {
    id: '20',
    text: "La règle des 2 minutes : si ça prend moins de 2 minutes, fais-le maintenant.",
    category: 'productivity',
    isPremium: false,
  },

  // MINDSET (10)
  {
    id: '21',
    text: "Ton état d'esprit détermine ta réalité. Change tes pensées, change ta vie.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '22',
    text: "L'échec n'est qu'une opportunité de recommencer de manière plus intelligente.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '23',
    text: "Ce que tu penses, tu le deviens. Ce que tu ressens, tu l'attires.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '24',
    text: "Grandis à travers ce que tu traverses.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '25',
    text: "Les obstacles ne bloquent pas le chemin, ils sont le chemin.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '26',
    text: "Ta zone de confort est un bel endroit, mais rien n'y pousse.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '27',
    text: "Pense en possibilités, pas en limitations.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '28',
    text: "L'attitude est une petite chose qui fait une grande différence.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '29',
    text: "Tu ne peux pas changer le vent, mais tu peux ajuster tes voiles.",
    category: 'mindset',
    isPremium: false,
  },
  {
    id: '30',
    text: "Chaque jour est une nouvelle page. Écris une belle histoire.",
    category: 'mindset',
    isPremium: false,
  },

  // SUCCESS (10)
  {
    id: '31',
    text: "Les gens qui réussissent font ce que les autres ne veulent pas faire.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '32',
    text: "Le succès est la somme de petits efforts répétés jour après jour.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '33',
    text: "Ne compare pas ton chapitre 1 au chapitre 20 de quelqu'un d'autre.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '34',
    text: "Le succès n'est pas une destination, c'est un voyage.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '35',
    text: "Investis en toi-même. C'est le meilleur investissement que tu puisses faire.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '36',
    text: "La réussite appartient à ceux qui y croient et qui agissent.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '37',
    text: "Tes résultats sont le reflet de tes actions quotidiennes.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '38',
    text: "Célèbre les petites victoires sur le chemin des grandes.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '39',
    text: "La persévérance bat le talent quand le talent ne persévère pas.",
    category: 'success',
    isPremium: false,
  },
  {
    id: '40',
    text: "Le succès commence par la décision d'essayer.",
    category: 'success',
    isPremium: false,
  },

  // DISCIPLINE (10)
  {
    id: '41',
    text: "La discipline est le pont entre tes objectifs et tes accomplissements.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '42',
    text: "Ce que tu fais aujourd'hui peut améliorer tous tes lendemains.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '43',
    text: "L'autodiscipline est le moteur de la réussite personnelle.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '44',
    text: "Fais-le maintenant. Parfois 'plus tard' devient 'jamais'.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '45',
    text: "La cohérence bat l'intensité. Montre-toi chaque jour.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '46',
    text: "Choisis la difficulté de la discipline ou la douleur du regret.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '47',
    text: "Les habitudes que tu construis aujourd'hui façonnent ton futur.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '48',
    text: "Sois plus fort que tes excuses.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '49',
    text: "Le self-control est la clé de la liberté.",
    category: 'discipline',
    isPremium: false,
  },
  {
    id: '50',
    text: "Engage-toi envers toi-même. Personne d'autre ne le fera pour toi.",
    category: 'discipline',
    isPremium: false,
  },
];
