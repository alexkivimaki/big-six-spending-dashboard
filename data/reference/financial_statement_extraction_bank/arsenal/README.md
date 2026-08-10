# Arsenal Financial Statement Extraction Bank

This folder documents how Arsenal's statements are structured for the club-finance dataset.

Current scope:

- extracted range currently covers:
  - `2008/09` to `2024/25`
- common structured workflow range remains:
  - `2011/12` onward

General Arsenal patterns observed:

- reporting currency is GBP
- values are disclosed in `GBP '000`
- stored values in the dataset must be converted to full GBP by multiplying by `1,000`
- Arsenal reports to a `31 May` year end
- Arsenal usually discloses the football revenue split explicitly with:
  - `Gate and other match day revenues`
  - `Broadcasting`
  - commercial-related lines that need mapping into one `commercial` bucket
- Arsenal often discloses:
  - `Retail`
  - `Retail and licensing`
  - `Licensing`
  rather than one clean commercial line
- player trading and property development can be disclosed separately and must be excluded from football revenue totals
- staff costs and player amortisation are available, but their page positions drift meaningfully across the long time range

Important Arsenal-specific caveats:

- for Arsenal, football revenue should exclude:
  - player trading
  - property development turnover
- the `commercial` bucket sometimes needs to be constructed from multiple disclosed lines
- later extracted seasons do not always yet carry explicit `profit before tax` and `net debt` evidence in the raw JSON, even when the clean dataset has been supplemented elsewhere
- from `2023/24` onward, women's UEFA income is separately disclosed and should be excluded where clearly separable

When adding more Arsenal seasons or revisiting existing ones:

1. Check whether retail / licensing is disclosed separately.
2. Confirm property development is excluded from football revenue.
3. Confirm whether women's football revenue is separately identifiable.
4. Record page drift immediately after extraction.
