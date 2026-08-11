export const DISPLAY_CURRENCY = {
  EUR: "EUR",
  GBP: "GBP",
  USD: "USD",
};

export const fxReference = {
  sourceName: "ECB euro foreign exchange reference rates",
  sourceUrl:
    "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html",
  referenceDate: "2026-08-11",
  ratesPerEuro: {
    EUR: 1,
    GBP: 0.85483,
    USD: 1.154,
  },
};

export const displayCurrencyOptions = [
  { id: DISPLAY_CURRENCY.EUR, label: "EUR" },
  { id: DISPLAY_CURRENCY.GBP, label: "GBP" },
  { id: DISPLAY_CURRENCY.USD, label: "USD" },
];
