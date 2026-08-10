# Data Dictionary

This document defines the main working schemas for the first viable collection pipeline.

## `club_season_transfers`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier such as `premier_league` or `la_liga`. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Season label in `YYYY/YY` format. |
| `season_start_year` | First calendar year of the season. |
| `window` | Transfer window label such as `summer`, `winter`, or `all`. |
| `gross_transfer_spend_eur` | Parsed transfer spend in euros where available. |
| `transfer_income_eur` | Parsed transfer income in euros where available. |
| `net_transfer_spend_eur` | Spend minus income in euros where available. |
| `incoming_transfer_count` | Count of incoming transfers in the parsed response. |
| `outgoing_transfer_count` | Count of outgoing transfers in the parsed response. |
| `source_name` | Source label, typically `transfermarkt_club_page`. |
| `source_endpoint` | Endpoint URL used for collection. |
| `collected_at_utc` | UTC timestamp for collection. |
| `confidence_level` | Confidence flag for automated parsing quality. |
| `notes` | Caveats or parsing remarks. |

## `player_transfers`

| Field | Description |
| --- | --- |
| `transfer_id` | Transfer record identifier if available. |
| `player_id` | Internal or source player identifier. |
| `player_name` | Human-readable player name. |
| `season` | Season label in `YYYY/YY` format. |
| `window` | Transfer window label. |
| `date` | Transfer date. |
| `buying_club_id` | Buying club identifier if available. |
| `buying_club_name` | Buying club name. |
| `selling_club_id` | Selling club identifier if available. |
| `selling_club_name` | Selling club name. |
| `fee_eur` | Parsed transfer fee in euros where available. |
| `fee_type` | Fee category such as `reported`, `estimated`, `loan_fee`, or `unknown`. |
| `transfer_type` | Deal type such as `permanent`, `loan`, or `free`. |
| `position` | Player position. |
| `age` | Player age at transfer time where available. |
| `source_name` | Source label, typically `transfermarkt_api`. |
| `source_endpoint` | Endpoint URL used for collection. |
| `collected_at_utc` | UTC timestamp for collection. |
| `confidence_level` | Confidence flag for parsing quality. |
| `notes` | Caveats or parsing remarks. |

## `club_season_wages`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier where relevant. |
| `league_name` | Human-readable league name where relevant. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Season label in `YYYY/YY` format. |
| `estimated_player_wages_eur` | Estimated player wages in euros. |
| `official_staff_costs_eur` | Official staff cost figure in euros where available. |
| `currency_original` | Original source currency. |
| `conversion_rate_to_eur` | Conversion rate used if a source was not already in euros. |
| `source_name` | Source name. |
| `source_url` | Source URL. |
| `date_accessed` | Source access date. |
| `evidence` | Evidence quote or page reference. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `club_season_finances`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier where relevant. |
| `league_name` | Human-readable league name where relevant. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Season label in `YYYY/YY` format. |
| `revenue_eur` | Total revenue in euros. |
| `matchday_revenue_eur` | Matchday revenue in euros. |
| `broadcasting_revenue_eur` | Broadcasting revenue in euros. |
| `commercial_revenue_eur` | Commercial revenue in euros. |
| `official_staff_costs_eur` | Official staff costs in euros. |
| `operating_profit_loss_eur` | Operating profit or loss in euros. |
| `profit_loss_before_tax_eur` | Profit or loss before tax in euros. |
| `net_debt_eur` | Net debt in euros. |
| `player_amortisation_eur` | Player amortisation expense in euros. |
| `profit_on_player_sales_eur` | Profit on player sales in euros. |
| `currency_original` | Original source currency. |
| `conversion_rate_to_eur` | Conversion rate used if applicable. |
| `source_name` | Source name. |
| `source_url` | Source URL. |
| `date_accessed` | Source access date. |
| `evidence` | Evidence quote or page reference. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `club_season_performance`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier where relevant. |
| `league_name` | Human-readable league name where relevant. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Season label in `YYYY/YY` format. |
| `league_position` | Final league position. |
| `points` | League points. |
| `wins` | League wins. |
| `draws` | League draws. |
| `losses` | League losses. |
| `goals_for` | Goals scored. |
| `goals_against` | Goals conceded. |
| `goal_difference` | Goal difference. |
| `trophies` | Trophy summary. |
| `champions_league_qualified` | Boolean qualification flag. |
| `source_name` | Source name. |
| `source_url` | Source URL. |
| `date_accessed` | Source access date. |
| `evidence` | Evidence quote or page reference. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `managers`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier where relevant. |
| `league_name` | Human-readable league name where relevant. |
| `manager_id` | Stable manager identifier. |
| `manager_name` | Human-readable manager name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `start_date` | Spell start date. |
| `end_date` | Spell end date. |
| `source_name` | Source name. |
| `source_url` | Source URL. |
| `date_accessed` | Source access date. |
| `evidence` | Evidence quote or page reference. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `ownership_eras`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier where relevant. |
| `league_name` | Human-readable league name where relevant. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `ownership_era` | Era label. |
| `owner_or_group_name` | Ownership entity name. |
| `start_date` | Era start date. |
| `end_date` | Era end date. |
| `source_name` | Source name. |
| `source_url` | Source URL. |
| `date_accessed` | Source access date. |
| `evidence` | Evidence quote or page reference. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `manager_history_clean`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `role_key` | Source role key such as `manager` or `caretaker_manager`. |
| `role_name` | Human-readable source role label. |
| `manager_id` | Stable manager identifier derived from name and birth date. |
| `manager_name` | Human-readable manager name. |
| `manager_date_of_birth` | Manager date of birth as shown on the source page. |
| `start_date` | Date the manager spell began. |
| `end_date` | Date the manager spell ended, if available. |
| `time_in_post_days` | Duration shown by the source page, converted to days where possible. |
| `matches` | Matches managed during the spell. |
| `ppg` | Points per game shown on the source page. |
| `source_name` | Source label, typically `transfermarkt_manager_history_page`. |
| `source_endpoint` | Source URL used for collection. |
| `collected_at_utc` | UTC collection timestamp. |
| `confidence_level` | Confidence flag for parsing quality. |
| `notes` | Caveats or contextual notes. |

## `club_season_manager_spells`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `role_key` | Source role key such as `manager` or `caretaker_manager`. |
| `role_name` | Human-readable source role label. |
| `season` | Season label in `YYYY/YY` format. |
| `season_start_year` | First calendar year of the season. |
| `season_end_year` | Second calendar year of the season. |
| `manager_id` | Stable manager identifier. |
| `manager_name` | Human-readable manager name. |
| `manager_date_of_birth` | Manager date of birth as shown on the source page. |
| `spell_start_date` | Original manager spell start date. |
| `spell_end_date` | Original manager spell end date, if available. |
| `overlap_start_date` | Start of the manager’s overlap with the season window. |
| `overlap_end_date` | End of the manager’s overlap with the season window. |
| `days_in_charge_in_season` | Number of overlapping days in that season. |
| `days_in_season` | Total number of days in the season window used for allocation. |
| `share_of_season` | Fraction of season days attributed to the manager. |
| `source_name` | Source label. |
| `source_endpoint` | Source URL. |
| `collected_at_utc` | UTC collection timestamp. |
| `confidence_level` | Confidence flag. |
| `notes` | Caveats or contextual notes. |

## `club_season_dashboard`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Season label in `YYYY/YY` format. |
| `gross_transfer_spend_eur` | Club-season gross transfer spend in euros. |
| `transfer_income_eur` | Club-season transfer income in euros. |
| `net_transfer_spend_eur` | Gross spend minus transfer income. |
| `estimated_player_wages_eur` | Estimated player wages in euros. |
| `official_staff_costs_eur` | Official staff costs in euros if available. |
| `raw_player_cost_eur` | Net transfer spend plus estimated player wages. |
| `league_position` | Final league position. |
| `points` | League points. |
| `cost_per_point` | Raw player cost divided by points. |
| `revenue_eur` | Official revenue in euros if available. |
| `wage_to_revenue_ratio` | Official staff costs divided by revenue if available. |
| `confidence_level` | Combined or inherited confidence indicator. |
| `notes` | Notes carried forward from source tables. |

## `achievement_rows_clean`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `achievement_season_label` | Original season or year label shown on the Transfermarkt achievements page. |
| `assigned_season` | Normalized club-season label used in this project. |
| `assigned_season_start_year` | First year of the assigned club season. |
| `assigned_season_end_year` | Second year of the assigned club season. |
| `achievement_name` | Achievement text shown by the source page. |
| `achievement_category` | Parsed category such as `league_title`, `fa_cup`, or `club_world_cup`. |
| `achievement_result` | Parsed result such as `winner`, `runner_up`, or `participant`. |
| `is_major_trophy` | Boolean flag for major trophy wins. |
| `assignment_method` | Rule used to convert the source label into a club-season. |
| `assignment_confidence` | Confidence level for the assignment. |
| `source_name` | Source label, typically `transfermarkt_achievements_page`. |
| `source_endpoint` | Source URL used for collection. |
| `collected_at_utc` | UTC collection timestamp. |
| `notes` | Caveats or mapping notes. |

## `club_season_achievements_clean`

| Field | Description |
| --- | --- |
| `league_key` | Stable internal league identifier. |
| `league_name` | Human-readable league name. |
| `club_id` | Stable internal club identifier. |
| `club_name` | Human-readable club name. |
| `season` | Normalized club-season label. |
| `season_start_year` | First year of the season. |
| `season_end_year` | Second year of the season. |
| `achievement_count_total` | Number of achievement rows assigned to the season. |
| `major_trophy_count` | Number of major trophy wins assigned to the season. |
| `achievement_names` | Pipe-delimited list of assigned achievements. |
| `major_trophies` | Pipe-delimited list of major trophy wins. |
| `source_name` | Source label. |
| `source_endpoint` | Source URL. |
| `collected_at_utc` | UTC collection timestamp. |
| `confidence_level` | Confidence flag for the season summary. |
| `notes` | Caveats or mapping notes. |
