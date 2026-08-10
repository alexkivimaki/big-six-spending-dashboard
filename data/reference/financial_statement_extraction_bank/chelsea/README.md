# Chelsea Financial Statement Extraction Bank

This folder documents how Chelsea's statements are structured for the club-finance dataset.

Current scope:

- extracted range currently covers:
  - `2011/12` to `2024/25`

General Chelsea patterns observed:

- reporting currency is GBP
- values are disclosed in `GBP '000`
- stored values in the dataset must be converted to full GBP by multiplying by `1,000`
- Chelsea reports to a `30 June` year end
- Chelsea usually discloses the football revenue split directly as:
  - `Matchday`
  - `Broadcasting`
  - `Commercial`
- staff-cost extraction is based on the employee-cost / wages-and-salaries note
- player amortisation is disclosed through intangible asset / player registration amortisation
- early Chelsea extractions include explicit `profit before tax` and `net debt` evidence pages; later raw rows do not always carry those page references even though the broad extraction is otherwise consistent

Important Chelsea-specific caveats:

- `2011/12` has a known reconciliation wrinkle:
  the category split is disclosed before deducting Chelsea Digital Media joint-venture turnover, so the category sum exceeds reported group turnover by `GBP 1,796,000`
- Chelsea commercial revenue may include:
  - hotel
  - stadium
  - retail
  - other non-matchday commercial operations
- women's team revenue is not separately disclosed in the Chelsea statements used so far, so the extracted turnover should be treated as potentially including inseparable women's activity

When adding more Chelsea seasons or revisiting existing ones:

1. Check whether the revenue split is still given directly as Matchday / Broadcasting / Commercial.
2. Check whether net debt is explicitly disclosed or only inferable.
3. Record if the commercial category wording changes.
4. Record any new disclosure about women’s football separately if it appears.
