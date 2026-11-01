from collections import defaultdict
from jurialmunkey.ftools import cached_property
from tmdbhelper_sync_floppy.dates import utc_timestamp
from tmdbhelper_sync_floppy.media import FloppyMedia
from tmdbhelper_sync_floppy.sync.state import FloppyWatchedState


class FloppySnapshot:
    def __init__(self, api, item_type):
        self.api = api
        self.item_type = item_type

    @property
    def media_type(self):
        return 'movie' if self.item_type == 'movie' else 'tv'

    def get_media_entries(self, media_type=None, status=None):
        return self.api.get_media(media_type or self.media_type, status=status)

    def get_media(self, entries):
        return [item for item in map(FloppyMedia, entries) if item.is_supported]

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        return {
            item.tmdb_id: self.get_entry_metadata(item)
            for item in self.get_media(self.get_media_entries())
        }

    @staticmethod
    def get_entry_metadata(item):
        progress = item.entry.get('progress')
        remaining = item.entry.get('episodes_left')
        aired = progress + remaining if progress is not None and remaining is not None else None
        return dict(item.record, aired_episodes=aired)

    def get_item_metadata(self, item):
        return self.get_metadata_for_id(item.tmdb_id)

    def get_metadata_for_id(self, tmdb_id):
        try:
            return dict(self.metadata[tmdb_id])
        except KeyError:
            # Titles that are not tracked (for example a watched episode of a show
            # that was later untracked) are absent from the media list.
            details = self.api.get_details(self.media_type, tmdb_id)
            record = self.get_entry_metadata(FloppyMedia(details))
            self.metadata[tmdb_id] = record
            return dict(record)


class FloppyWatchlistSnapshot(FloppySnapshot):
    def get_items(self):
        return [
            dict(
                item.record, listed_at=utc_timestamp(item.entry['created_at']),
                rank=rank, notes=item.entry.get('notes'))
            for rank, item in enumerate(self.get_media(self.get_media_entries(status=0)), 1)
        ]


class FloppyDroppedSnapshot(FloppySnapshot):
    def get_items(self):
        if self.item_type == 'movie':
            return []
        return [
            dict(
                item.record,
                hidden_at=utc_timestamp(item.entry.get('progressed_at') or item.entry['created_at']))
            for item in self.get_media(self.get_media_entries(status=4))
        ]


class FloppyWatchedSnapshot(FloppySnapshot):
    def get_states(self):
        return self.api.get_cached_snapshot(
            'watched_state', lambda: FloppyWatchedState(self.api).get_items())

    def get_watched_episode_keys(self, tmdb_id=None):
        """(tmdb_id, season, episode) of watched episodes, without metadata lookups."""
        return {
            (item.tmdb_id, item.record['season_number'], item.record['episode_number'])
            for item in self.get_media(self.get_states())
            if item.item_type == 'episode' and item.entry['watched']
            and (tmdb_id is None or item.tmdb_id == tmdb_id)
        }

    def get_items(self):
        media = self.get_media(self.get_states())
        item_types = ('movie',) if self.item_type == 'movie' else ('episode',)
        records = [
            self.get_record(item) for item in media
            if item.item_type in item_types and item.entry['watched']
        ]
        # Bucket aliases can identify the same TMDb episode. Count each episode once.
        records = list({
            (item['tmdb_id'], item['season_number'], item['episode_number']): item
            for item in sorted(records, key=lambda item: item['last_watched_at'] or '')
        }.values())
        if self.item_type == 'movie':
            return records
        shows = self.get_parents(records, 'show')
        # Every season of a fully watched show is complete, so its released
        # episode count is known without a season details request.
        complete = {item['tmdb_id'] for item in shows if item['plays']}
        return records + shows + self.get_parents(records, 'season', complete)

    def get_record(self, item):
        record = self.get_item_metadata(item)
        record.update({
            'item_type': item.item_type,
            'season_number': item.record['season_number'],
            'episode_number': item.record['episode_number'],
            'plays': item.entry['play_count'],
            'last_watched_at': utc_timestamp(item.entry['watched_at']),
        })
        return record

    def get_parents(self, records, item_type, complete=()):
        groups = defaultdict(list)
        for item in records:
            if item['season_number'] == 0:
                continue
            key = (item['tmdb_id'], item['season_number'] if item_type == 'season' else None)
            groups[key].append(item)
        return [
            self.get_parent(key, items, item_type, key[0] in complete)
            for key, items in groups.items()]

    def get_parent(self, key, records, item_type, complete=False):
        if item_type == 'show':
            aired = self.get_metadata_for_id(key[0]).get('aired_episodes')
        elif complete:
            aired = len(records)
        else:
            # Season detail returns the released count as max_progress.
            aired = self.api.get_details('tv', key[0], key[1]).get('max_progress')
        return dict(
            records[0], item_type=item_type, season_number=key[1], episode_number=None,
            plays=min(item['plays'] for item in records) if aired and len(records) >= aired else 0,
            watched_episodes=len(records),
            last_watched_at=max(
                (item['last_watched_at'] for item in records if item['last_watched_at']),
                default=None))


class FloppyCollectionSnapshot(FloppySnapshot):
    def get_items(self):
        entries = self.api.get_snapshot('collection')
        media = self.get_media(entries)
        records = [
            dict(
                item.record, last_collected_at=utc_timestamp(item.entry['collected_at']),
                last_updated_at=utc_timestamp(item.entry['updated_at']))
            for item in media
            if (item.item_type == 'movie') == (self.item_type == 'movie')
        ]
        records = list({
            (item['tmdb_id'], item['season_number'], item['episode_number']): item
            for item in sorted(records, key=lambda item: item['last_collected_at'] or '')
        }.values())
        if self.item_type == 'movie':
            return records
        return records + self.get_parents(records, 'show') + self.get_parents(records, 'season')

    def get_parents(self, records, item_type):
        groups = defaultdict(list)
        for item in records:
            if item['item_type'] != 'episode':
                continue
            key = (item['tmdb_id'], item['season_number'] if item_type == 'season' else None)
            groups[key].append(item)
        return [
            dict(
                dict(items[0], **self.get_metadata_for_id(key[0])),
                item_type=item_type, season_number=key[1], episode_number=None,
                last_collected_at=self.get_latest(items, 'last_collected_at'),
                last_updated_at=self.get_latest(items, 'last_updated_at'))
            for key, items in groups.items()
        ]

    @staticmethod
    def get_latest(items, key):
        return max((item[key] for item in items if item[key]), default=None)


class FloppyPlaybackSnapshot(FloppySnapshot):
    def get_items(self):
        entries = self.api.get_snapshot(
            'playback/progress', {'media_type': 'movie,episode', 'completed': 'false'})
        return [
            self.get_record(item) for item in self.get_media(entries)
            if (item.item_type == 'movie') == (self.item_type == 'movie')
            and item.entry['position_seconds'] > 0 and item.entry['duration_seconds']
        ]

    def get_record(self, item):
        record = self.get_item_metadata(item)
        record.update({key: value for key, value in item.record.items() if value is not None})
        record.update({
            'progress': min(100, item.entry['position_seconds'] * 100 / item.entry['duration_seconds']),
            'paused_at': utc_timestamp(item.entry['updated_at']),
            'id': '.'.join(str(value) for value in (
                item.item_type, item.tmdb_id,
                item.record['season_number'], item.record['episode_number'])),
        })
        return record


class FloppyNextEpisodesSnapshot(FloppySnapshot):
    def get_items(self):
        if self.item_type == 'movie':
            return []
        return [self.get_record(item) for item in self.get_media(self.get_media_entries())]

    @staticmethod
    def get_record(item):
        entry = item.entry
        next_episode = entry['next_episode'] if entry['status'] not in (2, 4) else None
        next_id = None
        if next_episode:
            next_id = f'tv.{item.tmdb_id}.{next_episode["season_number"]}.{next_episode["episode_number"]}'
        remaining = entry['episodes_left']
        return dict(
            item.record,
            aired_episodes=entry['progress'] + remaining if remaining is not None else None,
            next_episode_id=next_id,
            next_episode_aired_at=utc_timestamp(next_episode['air_date']) if next_episode else None)


class FloppyAllNextEpisodesSnapshot(FloppyNextEpisodesSnapshot):
    def get_items(self):
        if self.item_type == 'movie':
            return []
        from tmdbhelper_sync_floppy.episodes import FloppyEpisodes
        # Only episode identities are needed, not the full watched snapshot with
        # its metadata and per-season requests.
        watched_ids = FloppyWatchedSnapshot(self.api, 'show').get_watched_episode_keys()
        shows = [
            item for item in self.get_media(self.get_media_entries())
            if item.entry['status'] not in (0, 2, 4) and item.entry['next_episode']
        ]
        return [
            dict(record, upnext_episode_id=(
                f'tv.{record["tmdb_id"]}.{record["season_number"]}.{record["episode_number"]}'))
            for show in shows
            for record in FloppyEpisodes(self.api, show.tmdb_id, skip_hidden=True).get_records()
            if (record['tmdb_id'], record['season_number'], record['episode_number']) not in watched_ids
        ]
