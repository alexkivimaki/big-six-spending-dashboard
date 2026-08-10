# Master Financial Statement Extraction Bank

This is the single cross-club reference file for extracting football-finance data from annual reports.

It is designed to be read before starting a new club or season extraction. The goal is to help the extractor understand:

- how different clubs structure their statements
- where key revenue, wage, debt, and profit fields usually appear
- which adjustments and exclusions are needed
- which club-specific traps are most likely

This file should be updated whenever:

- a new club is extracted
- a new season is added
- a note label changes
- a debt method changes
- a previously unclear disclosure becomes clear

## Common Project Rules

- Use official annual reports / Companies House / official investor reports first.
- Treat report values as `full GBP` in the dataset, even when the statement discloses `GBP '000`.
- Exclude player trading from football revenue totals.
- Exclude property development turnover where separately disclosed.
- Do not invent women's revenue adjustments. Exclude only where separately disclosed and separable.
- Record page references and extraction caveats season by season.

## Club Overview

| Club | Current extracted range | Typical year end | Text quality | Revenue split style | Main recurring challenge |
|---|---|---:|---|---|---|
| Arsenal | 2008/09-2024/25 | 31 May | text PDF | matchday + broadcasting + commercial built from retail/licensing mappings | excluding property development and assembling commercial correctly |
| Chelsea | 2011/12-2024/25 | 30 June | text PDF | direct Matchday / Broadcasting / Commercial | commercial perimeter and occasional reconciliation quirks |
| Liverpool | 2011/12-2014/15 | 31 May | scanned PDF | direct Media / Matchday / Commercial | OCR reliability and estimated net debt from creditor notes |
| Manchester City | 2011/12-2013/14 | 31 May | mixed; older years scanned | direct split with multiple broadcasting lines | scanned PDFs and debt-note reconstruction |
| Manchester United | 2011/12, 2022/23-2024/25 | 30 June | older scanned; recent plc reports text-readable | plc segment split with direct commercial/broadcast/matchday | mixed source types and older scanned filings |
| Tottenham Hotspur | 2011/12 only | 30 June | older years scanned | note requires reclassification into matchday / broadcast / commercial | category mapping and scanned PDF OCR |

## Arsenal

### Broad Characteristics

- reporting entity used: Arsenal group accounts
- year end: `31 May`
- statement quality: text-readable PDFs
- revenue method:
  - football revenue is separated from player trading
  - property development turnover must be excluded
  - commercial revenue often has to be assembled from `commercial`, `retail`, `retail and licensing`, and `licensing`
- women’s football:
  - not separately disclosed in most seasons
  - women’s UEFA income is separately disclosed in `2023/24` and `2024/25` and should be excluded where separable
- debt:
  - some seasons use a debt-less-cash approach
  - some seasons rely on an analysis of changes in net debt note

### Season Map

| Season | FY end | Turnover p. | Staff p. | Amortisation p. | PBT p. | Net debt p. | Key season-specific note |
|---|---|---:|---:|---:|---:|---:|---|
| 2008/09 | 2009-05-31 | 31 | 39 | 38 | 41 | 47 | Exclude player trading and property development; compute debt from total debt less cash and short-term deposits |
| 2009/10 | 2010-05-31 | 32 | 39 | 38 | 42 | 48 | Same broad structure as prior year |
| 2010/11 | 2011-05-31 | 31 | 32 | 32 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2011/12 | 2012-05-31 | 30 | 31 | 31 | 34 | 41 | Layout becomes more compact |
| 2012/13 | 2013-05-31 | 30 | 31 | 31 | 34 | 41 | Similar to 2011/12 |
| 2013/14 | 2014-05-31 | 29 | 31 | 30 | 33 | 40 | Slight page drift |
| 2014/15 | 2015-05-31 | 31 | 32 | 32 | 35 | 49 | Debt note shifts materially later |
| 2015/16 | 2016-05-31 | 33 | 39 | 39 | 37 | 44 | PBT note appears earlier than some cost pages |
| 2016/17 | 2017-05-31 | 37 | 39 | 39 | 28 | 54 | Strong page drift; verify ordering carefully |
| 2017/18 | 2018-05-31 | 21 | 26 | 23 | 21 | 31 | Layout compresses substantially |
| 2018/19 | 2019-05-31 | 21 | 26 | 23 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2019/20 | 2020-05-31 | 25 | 27 | 26 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2020/21 | 2021-05-31 | 26 | 30 | 27 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2021/22 | 2022-05-31 | 22 | 27 | 26 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2022/23 | 2023-05-31 | 22 | 27 | 26 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2023/24 | 2024-05-31 | 26 | 32 | 30 |  |  | Women's UEFA income is separately disclosed and should be excluded |
| 2024/25 | 2025-05-31 | 31 | 34 | 32 |  |  | Women's UEFA income is separately disclosed; current season kept at medium confidence |

## Chelsea

### Broad Characteristics

- reporting entity used: Chelsea group accounts
- year end: `30 June`
- statement quality: text-readable PDFs
- revenue method:
  - revenue split is usually disclosed directly as `Matchday`, `Broadcasting`, `Commercial`
  - player trading is disclosed separately and should be excluded
- commercial perimeter:
  - may include hotel, stadium, retail, or broader commercial operations
- women’s football:
  - not separately disclosed in the extracted Chelsea seasons so far
  - extracted turnover may therefore include inseparable women’s activity
- debt:
  - early extracted seasons carry explicit net debt evidence
  - later seasons should be rechecked manually if debt fields need fresh re-extraction

### Season Map

| Season | FY end | Turnover p. | Staff p. | Amortisation p. | PBT p. | Net debt p. | Key season-specific note |
|---|---|---:|---:|---:|---:|---:|---|
| 2011/12 | 2012-06-30 | 15 | 16 | 16 | 17 | 25 | Category split exceeds reported turnover by GBP 1.796m because of Chelsea Digital Media joint-venture presentation |
| 2012/13 | 2013-06-30 | 15 | 16 | 16 | 19 | 26 | Direct revenue split available |
| 2013/14 | 2014-06-30 | 15 | 16 | 16 | 19 | 27 | Direct revenue split available |
| 2014/15 | 2015-06-30 | 16 | 17 | 17 | 20 | 29 | Page numbers drift up by roughly one page |
| 2015/16 | 2016-06-30 | 23 | 25 | 24 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2016/17 | 2017-06-30 | 22 | 24 | 23 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2017/18 | 2018-06-30 | 22 | 24 | 23 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2018/19 | 2019-06-30 | 22 | 24 | 23 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2019/20 | 2020-06-30 | 25 | 27 | 26 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2020/21 | 2021-06-30 | 28 | 30 | 29 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2021/22 | 2022-06-30 | 29 | 31 | 30 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2022/23 | 2023-06-30 | 33 | 35 | 34 |  |  | Current raw extraction lacks explicit PBT and debt evidence pages |
| 2023/24 | 2024-06-30 | 33 | 35 | 34 |  |  | Women's activity is not separately disclosed; commercial may include broader stadium/hotel operations |
| 2024/25 | 2025-06-30 | 29 | 31 | 30 |  |  | Women's activity is not separately disclosed; commercial may include broader stadium/hotel operations |

## Liverpool

### Broad Characteristics

- reporting entity used: Liverpool group / club accounts
- year end: `31 May`
- statement quality: scanned PDFs in the extracted seasons so far
- revenue method:
  - direct `Media`, `Matchday`, `Commercial` turnover note
- debt:
  - often not given as a single explicit net-debt line
  - can require combining bank loans and parent/group loans, then subtracting cash
- OCR risks:
  - commas
  - bracketed negatives
  - column order
  - current-year vs prior-year column confusion

### Season Map

| Season | FY end | Turnover p. | Staff p. | Amortisation p. | PBT p. | Debt pages | Key season-specific note |
|---|---|---:|---:|---:|---:|---|---|
| 2011/12 | 2012-05-31 | 17 | 18 | 18 | 21 | 30 | Shortened 10 month reporting period; explicit net debt line used |
| 2012/13 | 2013-05-31 | 17 | 18 | 18 | 11 | 25, 26 | Net debt estimated as current group undertaking loan + bank loan - cash |
| 2013/14 | 2014-05-31 | 18 | 19 | 19 | 12 | 26, 27 | Net debt estimated as current parent undertaking loan + bank loan - cash |
| 2014/15 | 2015-05-31 | 18 | 19 | 19 | 12 | 26, 27 | Profit on disposal of players is clearly disclosed; current-year debt sits mostly in current creditors |

## Manchester City

### Broad Characteristics

- reporting entity used so far: Manchester City Football Club Limited
- current extracted coverage includes `2011/12` to `2013/14`
- older years appear to be scanned PDFs
- revenue note uses a more granular split than some other clubs:
  - matchday / gate receipts
  - broadcasting split into UEFA and other television lines
  - other commercial activities
- broadcasting usually needs to be built by combining multiple lines
- debt likely requires note-based reconstruction rather than a clean single line in some seasons

### Current Known Guidance

- extracted:
  - `2011/12`
  - `2012/13`
  - `2013/14`
- when extracting future seasons, first look for:
  - profit and loss account
  - turnover note
  - staff numbers and costs note
  - financial instruments / borrowings note
  - balance sheet cash line

## Manchester United

### Broad Characteristics

- reporting sources are mixed:
  - older club filings are scanned
  - recent plc annual reports / 20-Fs are text-readable and richer
- recent plc reports give a strong direct split for:
  - matchday
  - broadcasting
  - commercial
- recent plc reports also give strong financing and debt disclosures
- comparability is generally best when using the plc annual report where available

### Current Known Guidance

- extracted:
  - `2011/12`
  - `2022/23`
  - `2023/24`
  - `2024/25`
- older `2012/13` to `2021/22` range still needs club-by-club scanned statement work

## Tottenham Hotspur

### Broad Characteristics

- older extracted statement is scanned
- Tottenham’s revenue note does not align perfectly with the standard taxonomy
- categories may need reclassification into:
  - matchday
  - broadcasting
  - commercial
- UEFA solidarity/prize money and domestic cup gate/prize lines may need judgment calls

### Current Known Guidance

- extracted:
  - `2011/12`
- when extracting future seasons, special attention is needed for category mapping rather than only OCR accuracy

## How Future AI Should Use This File

Before extracting a new season:

1. Read the club overview.
2. Read the relevant season row if the club already has extracted seasons.
3. Reuse the known note labels and page patterns as a first-pass map.
4. Check whether the new statement is closer to:
   - an early-year layout
   - a mid-period layout
   - a recent layout
5. Update this file immediately after the extraction if:
   - page numbers drift
   - note labels change
   - debt methodology changes
   - women’s revenue becomes separately disclosed
