# TMDbHelper Sync - Floppy

Standalone Floppy provider for TMDbHelper 6.20.0 or newer. This addon uses
TMDbHelper's provider interface version 3 and does not require changes to
TMDbHelper or another provider addon.

## Setup

1. Install `script.module.tmdbhelper.sync.floppy-0.1.0.zip` through Kodi's
   **Install from zip file** option and enable the addon.
2. Open this addon's settings and enter your Floppy server URL and API token
   from **Settings > Integrations** in Floppy. Include a reverse proxy path
   when applicable. A trailing `/api/v1` is accepted and normalized.
3. Run **TMDbHelper Sync - Floppy** from Program add-ons to select its sync
   features, or select Floppy in TMDbHelper's provider settings.
4. Browse the **Floppy** folder in TMDbHelper for user lists, watchlists,
   collection, watched titles and in-progress titles. Floppy user lists and
   watchlists are also available in library monitor options.

Use a current Floppy server exposing the canonical watched-state API and sync
contract 2 (`/api/v1/sync/bootstrap`, `sync/snapshot`, `sync/changes`). Older
servers without those endpoints cannot supply canonical watched sync. Floppy
may initially return `sync_initializing` while its background repair completes;
the provider leaves cached state intact and retries on the next sync.

A legacy account API token works. For a scoped integration token, enable
`watchlist:read`, `watchlist:write`, `progress:read`, `progress:write`,
`lists:read`, `lists:write`, `sync:read` and `scrobble:write` for all features.
Collection reads/writes use Floppy's watchlist scopes. No user-settings or token
management scope is needed.

Floppy is discovered once installed and enabled. Because this addon makes no
changes to TMDbHelper's catalogue, TMDbHelper cannot offer to install it before
it is installed. Kodi may show its normal third-party-provider confirmation.

## Behaviour

- Watched state, playcounts, watchlist, collection, resume positions, next
  episodes, all next episodes, aired episode counts and dropped shows use the
  existing sync columns and provider-specific cache identities.
- Watchlist membership means a Floppy tracking entry with **Planning** status.
  Removing watchlist membership removes only the exposed Planning consumption;
  it does not untrack a title and delete its history.
- Adding watched records a dated movie/episode play. Marking unwatched sets
  canonical watched state to false without deleting consumption history.
  Parent-show and season actions operate on their released episodes; marking a
  show or season watched skips episodes that are already watched. Specials
  are included when an individual special or season zero is addressed explicitly;
  normal whole-show actions and episode counts exclude specials.
- Floppy owns collection copies per movie or TV episode. Parent show/season
  membership is aggregated from episode copies. Adding a show/season collects
  its released episodes; removing collection membership removes the matching
  owned copies, including copies added outside this addon.
- Dropped shows are excluded from progress getters. Removing dropped status
  restores **In progress** on the matching dropped consumption.
- Playback percentages come from saved positions in seconds and known durations,
  independently of Floppy's episode-count tracking progress. Entries without
  a usable duration cannot be represented as a Kodi resume percentage.
- Scrobbling sends the start and stop events that TMDbHelper reports and uses
  its 80% completion threshold. Floppy saves the resume position on every stop,
  including incomplete ones. TMDbHelper does not report pauses to providers, so
  a position is saved when playback stops, not when it is paused.
- User lists are browsable regardless of which sync sources are selected.
  Editable static lists support add/remove through **Sync Options > Floppy**.
  Within an editable Floppy list the action removes from that list; elsewhere it
  offers a list picker. Smart lists and read-only shared lists remain browsable.
- Monitor references use `__api_floppy__` with numeric custom-list IDs or
  `watchlist/movie` and `watchlist/tv`. Monitoring retrieves all pages before
  returning items and performs no setup prompts or library writes.
- Only movies, TV shows, seasons and episodes with a resolved TMDb identity are
  exposed. Books, music, games and other Floppy media types are outside Kodi's
  movie/TV sync model. TV episode identities use the show's TMDb ID plus season
  and episode coordinates.

Snapshots refresh every ten minutes during normal sync. Successful writes
invalidate the relevant selected sync dependencies and clear the API client's
short-lived snapshots. A partially completed multi-item action also invalidates
the state it changed before reporting the failure.

Failed, unauthorized, cancelled, malformed or incomplete snapshots never replace
the previous sync cache. Unexpected response data fails only the Floppy
operation and is logged; it is not raised into TMDbHelper. An invalid server
URL is logged and treated as not configured. A successful empty snapshot clears the relevant columns.
Watched sync reads a bounded canonical baseline and replays concurrent changes;
it does not infer watched state solely from history, which would undo an explicit
unwatched assertion.

Floppy's movie history API can omit a Planning tracker once movie-play rows
exist. If it does not expose the exact Planning consumption, watchlist removal
reports a conflict and directs you to Floppy rather than deleting a potentially
colliding watch record. This is a server API limitation.

## Implementation

All implementation, settings, routes, actions, response mappings, pagination and
monitor integration live in `resources/lib/tmdbhelper_sync_floppy`.

- `provider.py`: provider registrations and activity refresh policy.
- `api.py`, `pagination.py`, `media.py`, `episodes.py`: HTTP transport,
  complete reads, media identities and released-episode enumeration.
- `sync/`: API-to-sync-record snapshots, sync types and sync database getters.
- `account/`: Floppy write operations and exact consumption/copy targeting.
- `actions/`: TMDbHelper action interfaces, dialogs and invalidation.
- `directories/`: containers, properties, output mappers and lazy routes.
- `monitor_lists.py`: list enumeration and library-builder records.
- `scrobbler.py`: playback reporting and pause-position persistence.

The module depends on TMDbHelper's shared interfaces; it does not import the
MDbList, Trakt or Kodi provider modules or patch their registrations.

## Verification

The implementation was checked using the installed TMDbHelper loader, directory
finalisation, mapper, sync and action base classes with stubbed Kodi APIs and
fixture HTTP responses. Checks cover complete/empty/failed snapshots, canonical
state replay, pagination, copy identities, movie/TV separation, special-episode
counts, list context actions, monitoring, partial writes and timestamp boundaries.
Python syntax, XML, absolute imports and whitespace were checked as well.

These are isolated checks. No live Floppy server or Kodi playback session was
used for end-to-end verification.

## References

- [Floppy](https://github.com/dannyvfilms/Floppy)
- [API documentation](https://github.com/dannyvfilms/Floppy/wiki/7.-API-and-MCP-Server)
- [Current API source](https://github.com/dannyvfilms/Floppy/tree/latest/src/api)
