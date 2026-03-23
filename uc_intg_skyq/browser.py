"""
SkyQ Media Browser for channels, favourites, and recordings.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import StatusCodes
from ucapi.api_definitions import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    Pagination,
    SearchOptions,
    SearchResults,
)

from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)

MEDIA_TYPE_ROOT = "root"
MEDIA_TYPE_CHANNELS = "channels"
MEDIA_TYPE_FAVOURITES = "favourites"
MEDIA_TYPE_RECORDINGS = "recordings"


async def browse(device: SkyQDevice, options: BrowseOptions) -> BrowseResults | StatusCodes:
    media_type = options.media_type or MEDIA_TYPE_ROOT

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

    channels = await device.get_channel_list()
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

    recordings = await device.get_recordings()
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

    channels = await device.get_channel_list()
    items.append(BrowseMediaItem(
        title="Channels",
        media_class=MediaClass.DIRECTORY,
        media_type=MEDIA_TYPE_CHANNELS,
        media_id="channels",
        can_browse=True,
        subtitle=f"{len(channels)} channels" if channels else "Browse channels",
    ))

    favourites = await device.get_favourite_list()
    if favourites:
        items.append(BrowseMediaItem(
            title="Favourites",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_FAVOURITES,
            media_id="favourites",
            can_browse=True,
            subtitle=f"{len(favourites)} favourites",
        ))

    recordings = await device.get_recordings()
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
            subtitle="Radio" if ch_type == "Radio" else "",
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
    page = options.paging.page if options.paging and options.paging.page else 1
    limit = options.paging.limit if options.paging and options.paging.limit else 20
    total = len(recordings)

    start = (page - 1) * limit
    end = min(start + limit, total)

    items: list[BrowseMediaItem] = []
    for rec in recordings[start:end]:
        title = getattr(rec, "title", "Recording")
        pvrid = getattr(rec, "pvrid", "")
        season = getattr(rec, "season", None)
        episode = getattr(rec, "episode", None)
        subtitle = _format_season_episode(season, episode, getattr(rec, "channelname", ""))

        items.append(BrowseMediaItem(
            title=title,
            media_class=MediaClass.VIDEO,
            media_type=MediaContentType.VIDEO,
            media_id=f"recording_{pvrid}",
            can_play=True,
            thumbnail=getattr(rec, "image_url", None),
            subtitle=subtitle,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Recordings",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_RECORDINGS,
            media_id="recordings",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


def _format_season_episode(season: int | None, episode: int | None, channel: str = "") -> str:
    parts = []
    if season and episode:
        parts.append(f"S{season:02d}E{episode:02d}")
    elif season:
        parts.append(f"Season {season}")
    elif episode:
        parts.append(f"Episode {episode}")
    if channel:
        parts.append(channel)
    return " | ".join(parts)
