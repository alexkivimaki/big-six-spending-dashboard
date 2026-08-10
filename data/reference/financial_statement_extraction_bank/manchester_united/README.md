# Manchester United Financial Statement Extraction Bank

This folder documents how Manchester United's statements are structured for the club-finance dataset.

Current scope:

- extracted range currently covers:
  - `2011/12`
  - `2012/13`
  - `2013/14`
  - `2014/15`
  - `2015/16`
  - `2021/22`
  - `2022/23`
  - `2023/24`
  - `2024/25`
- still unresolved in the current pass:
  - `2016/17`
  - `2017/18`
  - `2018/19`
  - `2019/20`
  - `2020/21`

General Manchester United patterns observed:

- reporting sources are mixed across the extraction range
- `2011/12` and `2021/22` onward can use Manchester United plc annual report / 20-F disclosures for a strong comparable revenue split
- `2012/13` to `2015/16` in the downloaded raw folder are scanned Manchester United Football Club Limited filings
- the older club-limited filings disclose turnover split directly as:
  - `Commercial`
  - `Broadcasting`
  - `Matchday`
- in the older club-limited filings, the commercial line is much narrower than the later plc commercial segment and appears largely tied to centrally negotiated sponsorship income
- staff costs and player amortisation are disclosed in the operating-expenses and staff / employee-cost notes
- the older club-limited filings do not present a clean Manchester United net-debt line
- for `2012/13` to `2015/16`, the debt approach used here estimates net debt as:
  - fellow-subsidiary senior secured notes
  - plus fellow-subsidiary secured term loan
  - less company cash / cash and cash equivalents

Important Manchester United-specific caveats:

- `2011/12` was taken from the plc annual report rather than the narrower club-limited filing for comparability
- `2012/13` to `2015/16` are scanned PDFs and require OCR plus manual checking
- the older club-limited revenue split is not directly comparable to the broader plc commercial segment used from `2021/22` onward
- `2016/17` to `2020/21` remain blocked in the current pass because the scanned filings require a longer OCR-and-page-mapping sweep than was completed here; partial scouting suggests the FRS 101 layout persists, but those seasons were not saved until each field and debt page could be verified to the same standard as the completed seasons

When adding more Manchester United seasons or resolving the blocked seasons:

1. Check the season row in `manchester_united_extraction_bank.csv`.
2. Confirm whether the source is a club-limited scanned filing or a plc / 20-F report.
3. For older club-limited filings, verify whether debt is still best estimated from fellow-subsidiary borrowings less cash.
4. Record any page drift immediately after each extraction.
