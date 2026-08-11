export const DISPLAY_CURRENCY = {
  EUR: "EUR",
  GBP: "GBP",
  USD: "USD",
};

export const fxReference = {
  sourceName: "ONS average sterling exchange rates",
  sourceUrl: "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/timeseries/thap/mret",
  secondarySourceUrl:
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/timeseries/auss/mret",
  referenceDate: "season-aware",
  description: "Currency views use exported season-level GBP/EUR and GBP/USD factors rather than a single spot date.",
};

export const displayCurrencyOptions = [
  { id: DISPLAY_CURRENCY.EUR, label: "EUR" },
  { id: DISPLAY_CURRENCY.GBP, label: "GBP" },
  { id: DISPLAY_CURRENCY.USD, label: "USD" },
];
