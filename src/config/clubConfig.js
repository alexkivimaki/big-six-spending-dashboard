export const clubConfigs = [
  {
    id: "arsenal",
    slug: "arsenal",
    name: "Arsenal",
    shortName: "Arsenal",
    initials: "ARS",
    colors: {
      primary: "#E1261C",
      secondary: "#F7D9D5",
      ink: "#71140D",
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
      secondary: "#DBE9FA",
      ink: "#08284A",
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
      primary: "#C8102E",
      secondary: "#F7D7DE",
      ink: "#641020",
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
      secondary: "#DFF0FB",
      ink: "#214867",
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
      primary: "#DA291C",
      secondary: "#F8DCD8",
      ink: "#741912",
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
      secondary: "#DEE6FA",
      ink: "#0A1538",
    },
    crest: null,
  },
];

export const clubConfigById = Object.fromEntries(clubConfigs.map((club) => [club.id, club]));
export const clubConfigBySlug = Object.fromEntries(clubConfigs.map((club) => [club.slug, club]));
