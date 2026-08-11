export const clubConfigs = [
  {
    id: "arsenal",
    slug: "arsenal",
    name: "Arsenal",
    shortName: "Arsenal",
    initials: "ARS",
    colors: {
      primary: "#E63946",
      secondary: "#FFF1F2",
      ink: "#7F1D1D",
    },
    visuals: {
      marker: {
        kind: "cannon",
        fill: "#E63946",
        stroke: "#E63946",
      },
      chart: {
        line: "#E63946",
        fill: "#E63946",
        stroke: "#E63946",
        halo: null,
      },
      identity: {
        background: "#FFF1F2",
        border: "#F8C1C6",
        fill: "#E63946",
        stroke: "#E63946",
      },
    },
    crest: null,
  },
  {
    id: "chelsea",
    slug: "chelsea",
    name: "Chelsea",
    shortName: "Chelsea",
    initials: "CHE",
    colors: {
      primary: "#034694",
      secondary: "#E8F0FF",
      ink: "#08284A",
    },
    visuals: {
      marker: {
        kind: "circle",
        fill: "#034694",
        stroke: "#034694",
      },
      chart: {
        line: "#034694",
        fill: "#034694",
        stroke: "#034694",
        halo: null,
      },
      identity: {
        background: "#E8F0FF",
        border: "#BBD0F1",
        fill: "#034694",
        stroke: "#034694",
      },
    },
    crest: null,
  },
  {
    id: "liverpool",
    slug: "liverpool",
    name: "Liverpool",
    shortName: "Liverpool",
    initials: "LIV",
    colors: {
      primary: "#8B1E2D",
      secondary: "#FCECEE",
      ink: "#5C1520",
    },
    visuals: {
      marker: {
        kind: "circle",
        fill: "#8B1E2D",
        stroke: "#8B1E2D",
      },
      chart: {
        line: "#8B1E2D",
        fill: "#8B1E2D",
        stroke: "#8B1E2D",
        halo: null,
      },
      identity: {
        background: "#FCECEE",
        border: "#E7BFC7",
        fill: "#8B1E2D",
        stroke: "#8B1E2D",
      },
    },
    crest: null,
  },
  {
    id: "manchester_city",
    slug: "manchester-city",
    name: "Manchester City",
    shortName: "Man City",
    initials: "MCI",
    colors: {
      primary: "#6CABDD",
      secondary: "#E8F5FF",
      ink: "#214867",
    },
    visuals: {
      marker: {
        kind: "circle",
        fill: "#6CABDD",
        stroke: "#6CABDD",
      },
      chart: {
        line: "#6CABDD",
        fill: "#6CABDD",
        stroke: "#6CABDD",
        halo: null,
      },
      identity: {
        background: "#E8F5FF",
        border: "#C2DCF0",
        fill: "#6CABDD",
        stroke: "#6CABDD",
      },
    },
    crest: null,
  },
  {
    id: "manchester_united",
    slug: "manchester-united",
    name: "Manchester United",
    shortName: "Man United",
    initials: "MUN",
    colors: {
      primary: "#F5A623",
      secondary: "#FFF5E5",
      ink: "#7A4A00",
    },
    visuals: {
      marker: {
        kind: "circle",
        fill: "#F5A623",
        stroke: "#F5A623",
      },
      chart: {
        line: "#F5A623",
        fill: "#F5A623",
        stroke: "#F5A623",
        halo: null,
      },
      identity: {
        background: "#FFF5E5",
        border: "#F4D28D",
        fill: "#F5A623",
        stroke: "#F5A623",
      },
    },
    crest: null,
  },
  {
    id: "tottenham_hotspur",
    slug: "tottenham-hotspur",
    name: "Tottenham Hotspur",
    shortName: "Spurs",
    initials: "TOT",
    colors: {
      primary: "#132257",
      secondary: "#EEF3FF",
      ink: "#132257",
    },
    visuals: {
      marker: {
        kind: "circle",
        fill: "#FFFFFF",
        stroke: "#132257",
      },
      chart: {
        line: "#FFFFFF",
        fill: "#FFFFFF",
        stroke: "#132257",
        halo: "#132257",
      },
      identity: {
        background: "#EEF3FF",
        border: "#C6D2EE",
        fill: "#FFFFFF",
        stroke: "#132257",
      },
    },
    crest: null,
  },
];

export const clubConfigById = Object.fromEntries(clubConfigs.map((club) => [club.id, club]));
export const clubConfigBySlug = Object.fromEntries(clubConfigs.map((club) => [club.slug, club]));
