export const REGIONS = {
  za: { label: "South Africa", peakSun: 5.5 },
  au: { label: "Australia", peakSun: 4.8 },
  uk: { label: "United Kingdom", peakSun: 2.8 },
  us: { label: "United States", peakSun: 4.5 },
  eu: { label: "Europe (Central)", peakSun: 3.5 },
  me: { label: "Middle East / MENA", peakSun: 6.0 },
} as const;

export type RegionKey = keyof typeof REGIONS;

