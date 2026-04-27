# Big Six Spending Dashboard

Interactive local React/Vite dashboard for comparing Premier League Big Six club spending from 2008/09 to 2025/26.

## What it includes

- Club selector: Arsenal, Manchester City, Manchester United, Chelsea, Liverpool, Tottenham Hotspur
- Season range controls
- Metric selector:
  - Gross transfer spend
  - Transfer income
  - Net transfer spend
  - Estimated wages
  - Raw player-cost estimate
- Line/bar chart toggle
- Period totals table

All figures are shown in rounded €m.

## How to run locally

1. Install Node.js if you do not already have it:
   https://nodejs.org/

2. Open a terminal in this project folder.

3. Install dependencies:

```bash
npm install
```

4. Start the local development server:

```bash
npm run dev
```

5. Open the local URL shown in the terminal, usually:

```text
http://localhost:5173
```

## How to build a shareable static version

Run:

```bash
npm run build
```

The static site will be created in the `dist` folder. You can upload that folder to Netlify, Vercel, GitHub Pages or another static hosting service.

## How to publish on GitHub Pages

This project now includes:

- `vite.config.js` with a relative asset base for static hosting
- `.github/workflows/deploy.yml` to build and deploy automatically with GitHub Actions

To publish it:

1. Create a new empty GitHub repository, for example `big-six-spending-dashboard`.
2. In this project folder, initialize Git and connect it to GitHub:

```bash
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/big-six-spending-dashboard.git
git push -u origin main
```

3. In GitHub, open the repository and go to:

```text
Settings -> Pages
```

4. Under `Build and deployment`, choose `GitHub Actions`.

5. Wait for the `Deploy Dashboard` workflow to finish.

Your public link will then be:

```text
https://YOUR_USERNAME.github.io/big-six-spending-dashboard/
```

## Data note

The transfer and wage data are based on the dataset assembled in the ChatGPT analysis. Transfer figures are more reliable than wage figures. Wage figures are estimated player payrolls and should be treated as directional rather than audited accounting data.
