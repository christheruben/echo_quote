export const CURRENCIES = {
  ZAR: { sym: "R", installPerW: 18.0, elecRate: 3.5 },
  AUD: { sym: "A$", installPerW: 1.1, elecRate: 0.32 },
  GBP: { sym: "£", installPerW: 1.3, elecRate: 0.28 },
  USD: { sym: "$", installPerW: 1.0, elecRate: 0.15 },
  EUR: { sym: "€", installPerW: 1.15, elecRate: 0.25 },
} as const;

export type CurrencyKey = keyof typeof CURRENCIES;