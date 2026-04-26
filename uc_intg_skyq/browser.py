"""
SkyQ Media Browser for channels, favourites, and recordings.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import base64
import logging
from datetime import datetime, timezone

from ucapi import StatusCodes
from ucapi.api_definitions import Pagination
from ucapi.media_player import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    SearchOptions,
    SearchResults,
)

from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)

MEDIA_TYPE_ROOT = "root"
MEDIA_TYPE_CHANNELS = "channels"
MEDIA_TYPE_FAVOURITES = "favourites"
MEDIA_TYPE_RECORDINGS = "recordings"
MEDIA_TYPE_SERIES = "series"
SERIES_ID_PREFIX = "series_"


async def browse(device: SkyQDevice, options: BrowseOptions) -> BrowseResults | StatusCodes:
    media_type = options.media_type or MEDIA_TYPE_ROOT
    media_id = options.media_id or ""

    if media_type == MEDIA_TYPE_SERIES or media_id.startswith(SERIES_ID_PREFIX):
        return await _browse_series(device, options)

    if media_type == MEDIA_TYPE_ROOT or (options.media_id is None and options.media_type is None):
        return await _browse_root(device)

    if media_type == MEDIA_TYPE_CHANNELS:
        return await _browse_channels(device, options)

    if media_type == MEDIA_TYPE_FAVOURITES:
        return await _browse_favourites(device, options)

    if media_type == MEDIA_TYPE_RECORDINGS:
        return await _browse_recordings(device, options)

    return StatusCodes.NOT_FOUND


async def search(device: SkyQDevice, options: SearchOptions) -> SearchResults | StatusCodes:
    query = options.query.lower()
    results: list[BrowseMediaItem] = []

    channels, recordings = await asyncio.gather(
        device.get_channel_list(),
        device.get_recordings(),
    )

    for ch in channels:
        name = getattr(ch, "channelname", "") or ""
        if query in name.lower():
            ch_no = getattr(ch, "channelno", "")
            results.append(BrowseMediaItem(
                title=f"{ch_no} - {name}" if ch_no else name,
                media_class=MediaClass.CHANNEL,
                media_type=MediaContentType.CHANNEL,
                media_id=f"channel_{ch_no}",
                can_play=True,
                thumbnail=getattr(ch, "channelimageurl", None),
            ))

    for rec in recordings:
        title = getattr(rec, "title", "") or ""
        if query in title.lower():
            pvrid = getattr(rec, "pvrid", "")
            season = getattr(rec, "season", None)
            episode = getattr(rec, "episode", None)
            subtitle = _format_season_episode(season, episode, getattr(rec, "channelname", ""))
            results.append(BrowseMediaItem(
                title=title,
                media_class=MediaClass.VIDEO,
                media_type=MediaContentType.VIDEO,
                media_id=f"recording_{pvrid}",
                can_play=True,
                thumbnail=getattr(rec, "image_url", None),
                subtitle=subtitle,
            ))

    return SearchResults(
        media=results,
        pagination=Pagination(page=1, limit=len(results), count=len(results)),
    )


async def _browse_root(device: SkyQDevice) -> BrowseResults:
    items: list[BrowseMediaItem] = []

    channels, favourites, recordings = await asyncio.gather(
        device.get_channel_list(),
        device.get_favourite_list(),
        device.get_recordings(),
    )

    items.append(BrowseMediaItem(
        title="Channels",
        media_class=MediaClass.DIRECTORY,
        media_type=MEDIA_TYPE_CHANNELS,
        media_id="channels",
        can_browse=True,
        subtitle=f"{len(channels)} channels" if channels else "Browse channels",
    ))

    if favourites:
        items.append(BrowseMediaItem(
            title="Favourites",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_FAVOURITES,
            media_id="favourites",
            can_browse=True,
            subtitle=f"{len(favourites)} favourites",
        ))

    if recordings:
        items.append(BrowseMediaItem(
            title="Recordings",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_RECORDINGS,
            media_id="recordings",
            can_browse=True,
            subtitle=f"{len(recordings)} recordings",
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title=device.name,
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_ROOT,
            media_id="root",
            can_browse=True,
            can_search=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_channels(device: SkyQDevice, options: BrowseOptions) -> BrowseResults:
    channels = await device.get_channel_list()
    page = options.paging.page if options.paging and options.paging.page else 1
    limit = options.paging.limit if options.paging and options.paging.limit else 50
    total = len(channels)

    start = (page - 1) * limit
    end = min(start + limit, total)

    items: list[BrowseMediaItem] = []
    for ch in channels[start:end]:
        ch_no = getattr(ch, "channelno", "")
        name = getattr(ch, "channelname", f"Channel {ch_no}")
        ch_type = getattr(ch, "channeltype", "")
        items.append(BrowseMediaItem(
            title=f"{ch_no} - {name}" if ch_no else name,
            media_class=MediaClass.CHANNEL,
            media_type=MediaContentType.CHANNEL,
            media_id=f"channel_{ch_no}",
            can_play=True,
            thumbnail=getattr(ch, "channelimageurl", None),
            subtitle="Radio" if ch_type == "Radio" else None,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Channels",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_CHANNELS,
            media_id="channels",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_favourites(device: SkyQDevice, options: BrowseOptions) -> BrowseResults:
    favourites = await device.get_favourite_list()
    page = options.paging.page if options.paging and options.paging.page else 1
    limit = options.paging.limit if options.paging and options.paging.limit else 50
    total = len(favourites)

    start = (page - 1) * limit
    end = min(start + limit, total)

    items: list[BrowseMediaItem] = []
    for fav in favourites[start:end]:
        ch_no = getattr(fav, "channelno", "") or getattr(fav, "lcn", "")
        name = getattr(fav, "channelname", f"Channel {ch_no}")
        items.append(BrowseMediaItem(
            title=f"{ch_no} - {name}" if ch_no else name,
            media_class=MediaClass.CHANNEL,
            media_type=MediaContentType.CHANNEL,
            media_id=f"channel_{ch_no}",
            can_play=True,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Favourites",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_FAVOURITES,
            media_id="favourites",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_recordings(device: SkyQDevice, options: BrowseOptions) -> BrowseResults:
    recordings = await device.get_recordings()
    grouped = _group_recordings_by_title(recordings)

    items: list[BrowseMediaItem] = []
    for title, recs in grouped:
        if len(recs) > 1:
            items.append(BrowseMediaItem(
                title=title,
                media_class=MediaClass.DIRECTORY,
                media_type=MEDIA_TYPE_SERIES,
                media_id=_encode_series_id(title),
                can_browse=True,
                thumbnail=getattr(recs[0], "image_url", None),
                subtitle=f"{len(recs)} episodes",
            ))
        else:
            items.append(_recording_leaf(recs[0]))

    page = options.paging.page if options.paging and options.paging.page else 1
    limit = options.paging.limit if options.paging and options.paging.limit else 50
    total = len(items)
    start = (page - 1) * limit
    end = min(start + limit, total)

    return BrowseResults(
        media=BrowseMediaItem(
            title="Recordings",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_RECORDINGS,
            media_id="recordings",
            can_browse=True,
            items=items[start:end],
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_series(device: SkyQDevice, options: BrowseOptions) -> BrowseResults | StatusCodes:
    media_id = options.media_id or ""
    try:
        title = _decode_series_id(media_id)
    except (ValueError, UnicodeDecodeError):
        return StatusCodes.NOT_FOUND

    recordings = await device.get_recordings()
    episodes = [r for r in recordings if (getattr(r, "title", "") or "") == title]
    if not episodes:
        return StatusCodes.NOT_FOUND
    episodes.sort(key=_episode_sort_key)

    items = [_episode_leaf(r) for r in episodes]
    return BrowseResults(
        media=BrowseMediaItem(
            title=title,
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_SERIES,
            media_id=media_id,
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


# -- Helpers -------------------------------------------------------------------


def _group_recordings_by_title(recordings) -> list[tuple[str, list]]:
    groups: dict[str, list] = {}
    for rec in recordings:
        title = getattr(rec, "title", "") or "Unknown"
        groups.setdefault(title, []).append(rec)
    return sorted(groups.items(), key=lambda kv: kv[0].lower())


def _recording_leaf(rec) -> BrowseMediaItem:
    title = getattr(rec, "title", "Recording")
    pvrid = getattr(rec, "pvrid", "")
    season = getattr(rec, "season", None)
    episode = getattr(rec, "episode", None)
    return BrowseMediaItem(
        title=title,
        media_class=MediaClass.VIDEO,
        media_type=MediaContentType.VIDEO,
        media_id=f"recording_{pvrid}",
        can_play=True,
        thumbnail=getattr(rec, "image_url", None),
        subtitle=_format_season_episode(season, episode, getattr(rec, "channelname", "")),
    )


def _episode_leaf(rec) -> BrowseMediaItem:
    pvrid = getattr(rec, "pvrid", "")
    season = getattr(rec, "season", None)
    episode = getattr(rec, "episode", None)
    starttime = getattr(rec, "starttime", None)

    if season and episode:
        try:
            label = f"S{int(season):02d}E{int(episode):02d}"
        except (TypeError, ValueError):
            label = f"S{season}E{episode}"
    elif episode:
        label = f"Episode {episode}"
    elif isinstance(starttime, datetime):
        label = starttime.strftime("%Y-%m-%d")
    else:
        label = getattr(rec, "title", "Episode")

    return BrowseMediaItem(
        title=label,
        media_class=MediaClass.VIDEO,
        media_type=MediaContentType.VIDEO,
        media_id=f"recording_{pvrid}",
        can_play=True,
        thumbnail=getattr(rec, "image_url", None),
        subtitle=getattr(rec, "channelname", None) or None,
    )


def _episode_sort_key(rec) -> tuple[int, int, datetime]:
    season = _safe_int(getattr(rec, "season", None))
    episode = _safe_int(getattr(rec, "episode", None))
    starttime = getattr(rec, "starttime", None)
    if not isinstance(starttime, datetime):
        starttime = datetime.min.replace(tzinfo=timezone.utc)
    return (season, episode, starttime)


def _safe_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _encode_series_id(title: str) -> str:
    payload = base64.urlsafe_b64encode(title.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{SERIES_ID_PREFIX}{payload}"


def _decode_series_id(media_id: str) -> str:
    payload = media_id.removeprefix(SERIES_ID_PREFIX)
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding).decode("utf-8")


def _format_season_episode(season: int | None, episode: int | None, channel: str = "") -> str | None:
    parts = []
    if season and episode:
        try:
            parts.append(f"S{int(season):02d}E{int(episode):02d}")
        except (TypeError, ValueError):
            parts.append(f"S{season}E{episode}")
    elif season:
        parts.append(f"Season {season}")
    elif episode:
        parts.append(f"Episode {episode}")
    if channel:
        parts.append(channel)
    return " | ".join(parts) if parts else None
