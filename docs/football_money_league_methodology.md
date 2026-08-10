# Football Money League Methodology

This project maintains an independent football revenue dataset inspired by the Deloitte Football Money League style. It is not an official Deloitte dataset.

## Core revenue categories

- `matchday`
  Gate receipts, season tickets, memberships, hospitality, and other matchday-related income.
- `broadcast`
  Domestic league distributions, domestic cup distributions, UEFA or other continental competition distributions, and FIFA Club World Cup distributions or prize money recognized in the financial period.
- `commercial`
  Sponsorship, merchandising, retail, licensing, tours, museum, non-matchday events, and other commercial operations.

## Exclusions

- player or coach transfer fees
- VAT and other sales-related taxes where identifiable
- deferred or accrued income outside the reported period where identifiable
- women’s team revenue for now where it is separately identifiable

## Important caveats

- Clubs classify revenue differently, so some mapping decisions may require notes.
- Non-matchday stadium events may appear in commercial revenue.
- Women’s team revenue may be included in consolidated club or group figures.
- Group reporting perimeter varies by club, especially where multiple entities exist.
- Some categories may require reclassification to fit the standardized methodology.

## Working rule

If the disclosed classification is ambiguous, do not guess. Keep the field null or preserve the disclosed label through notes and lower the confidence level.
