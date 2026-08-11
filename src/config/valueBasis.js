export const VALUE_BASIS = {
  nominal: "nominal",
  inflationAdjusted: "inflation-adjusted",
};

export const inflationConfig = {
  available: true,
  baseSeason: "2025/26",
  description: "Inflation-adjusted values are restated to 2025/26 prices using ONS CPI.",
  sourceName: "ONS CPI INDEX 00: ALL ITEMS 2015=100 (D7BT)",
  sourceUrl: "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23?lang=english",
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
