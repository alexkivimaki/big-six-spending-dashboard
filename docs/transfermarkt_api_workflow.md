# Transfermarkt API Workflow

The API workflow is now secondary for transfer totals. The preferred path for club-season transfer totals is the direct club transfers page scraper.

## How it is used

The local API is intended mainly for:

- player transfer history
- market values
- club and player metadata

It is not the primary source for:

- club-season transfer totals
- wages
- official revenue
- official staff costs
- verified league performance tables

Those should come from other sources and workflows.

## Endpoint templates

Endpoint paths are stored in [config/transfermarkt_api.example.json](/Users/alexkivimaki/big-six-spending-dashboard/config/transfermarkt_api.example.json:1). The collector scripts build request URLs from:

- `base_url`
- `club_transfers_endpoint_template`
- `club_players_endpoint_template`
- `player_transfers_endpoint_template`
- `market_values_endpoint_template`

## Important setup step

Before collecting data:

1. Start the local Transfermarkt API service.
2. Open its Swagger or OpenAPI documentation.
3. Confirm the actual endpoint paths and query parameters.
4. Update `config/transfermarkt_api.example.json` if the local implementation differs.

Different Transfermarkt API wrappers can expose slightly different routes, so the endpoint templates should be treated as configurable rather than guaranteed.

## Current compatibility note

The `felipeall/transfermarkt-api` project exposes:

- `/clubs/{club_id}/players`
- `/players/{player_id}/transfers`
- `/players/{player_id}/market_value`

It does not expose a direct `/clubs/{club_id}/transfers` route in the version currently checked locally. That is why the preferred transfer-total workflow now uses direct club page scraping instead of API-based reconstruction.
