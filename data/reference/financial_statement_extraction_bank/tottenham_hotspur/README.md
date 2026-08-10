# Tottenham Hotspur Financial Statement Extraction Bank

This folder documents how Tottenham Hotspur's statements are structured for the club-finance dataset.

Current scope:

- working extraction range starts at `2011/12`
- extracted so far:
  - `2011/12`
  - `2012/13`
  - `2013/14`
  - `2014/15`
  - `2015/16`
  - `2016/17`

General Tottenham patterns observed so far:

- reporting currency is GBP
- values are disclosed in `GBP '000`
- stored values in the dataset must be converted to full GBP by multiplying by `1,000`
- Tottenham reports to a `30 June` year end
- the revenue note shifts across the range:
  - `2011/12` uses a more granular split that requires reclassification
  - `2012/13` and `2013/14` use direct `Match receipts | TV and media | Commercial`
  - `2014/15` to `2016/17` separately disclose `UEFA prize money`, which should be grouped with broadcasting
- older statements are image-based PDFs, so evidence often requires page rendering or OCR cache review
- staff costs are usually available directly in note `5`
- player-sale profit is available from `Profit on disposal of intangible fixed assets`
- net debt / net cash is usually available directly in a late commitments / financing note

Important Tottenham-specific caveats:

- Tottenham’s revenue taxonomy does not perfectly match the project buckets in every season
- `UEFA prize money` should be grouped with `broadcast_revenue_original` for comparability
- `2014/15` explicitly says prior-year revenue was re-analysed to align with common industry practice
- `2012/13` to `2014/15` disclose a combined football-trading operating-expense line rather than a clean player-amortisation line, so `player_amortisation_original` should remain `null` unless a cleaner disclosure is found
- page numbers drift gradually, so note numbering should be checked season by season rather than assumed

When adding more Tottenham seasons:

1. Check whether `UEFA prize money` is still split out separately from `TV and media`.
2. Prefer the revenue note over strategic-report prose where both are available.
3. Distinguish explicit `net cash/(debt)` disclosures from broader financing commentary.
4. Record page drift and any note-label changes immediately after extraction.
