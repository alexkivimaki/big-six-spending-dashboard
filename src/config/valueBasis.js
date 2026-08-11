export const VALUE_BASIS = {
  nominal: "nominal",
  inflationAdjusted: "inflation-adjusted",
};

export const inflationConfig = {
  available: false,
  baseSeason: "2025/26",
  description: "Inflation-adjusted values are not available yet because no finalized price index series has been exported into the app.",
};

export const valueBasisOptions = [
  {
    id: VALUE_BASIS.nominal,
    label: "Nominal",
    description: "Reported season-by-season money values.",
    disabled: false,
  },
  {
    id: VALUE_BASIS.inflationAdjusted,
    label: "Inflation adjusted",
    description: `Adjusted to ${inflationConfig.baseSeason} prices.`,
    disabled: !inflationConfig.available,
  },
];
