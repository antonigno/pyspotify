from __future__ import unicode_literals

import spotify
from spotify import Album, Error, ErrorType, ffi, lib, Loadable
from spotify.utils import IntEnum, make_enum, to_bytes, to_unicode


__all__ = [
    'LocalTrack',
    'Track',
    'TrackAvailability',
    'TrackOfflineStatus',
]


class Track(Loadable):
    """A Spotify track."""

    def __init__(self, sp_track, add_ref=True):
        if add_ref:
            lib.sp_track_add_ref(sp_track)
        self.sp_track = ffi.gc(sp_track, lib.sp_track_release)

    @property
    def is_loaded(self):
        """Whether the track's data is loaded."""
        return bool(lib.sp_track_is_loaded(self.sp_track))

    @property
    def error(self):
        """An :class:`ErrorType` associated with the track.

        Check to see if there was problems loading the track.
        """
        return ErrorType(lib.sp_track_error(self.sp_track))

    @property
    def offline_status(self):
        """The :class:`TrackOfflineStatus` of the track.

        The :attr:`~SessionCallbacks.metadata_updated` callback is called when
        the offline status changes.
        """
        Error.maybe_raise(self.error)
        # TODO What happens here if the track is unloaded?
        return TrackOfflineStatus(
            lib.sp_track_offline_get_status(self.sp_track))

    @property
    def availability(self):
        """The :class:`TrackAvailability` of the track."""
        if spotify.session_instance is None:
            raise RuntimeError('Session must be initialized')
        Error.maybe_raise(self.error)
        # TODO What happens here if the track is unloaded?
        return TrackAvailability(lib.sp_track_get_availability(
            spotify.session_instance.sp_session, self.sp_track))

    @property
    def is_local(self):
        """Whether the track is a local track.

        Will always return :class:`None` if the track isn't loaded.
        """
        if spotify.session_instance is None:
            raise RuntimeError('Session must be initialized')
        Error.maybe_raise(self.error)
        if not self.is_loaded:
            return None
        return bool(lib.sp_track_is_local(
            spotify.session_instance.sp_session, self.sp_track))

    @property
    def is_autolinked(self):
        """Whether the track is a autolinked to another track.

        Will always return :class:`None` if the track isn't loaded.

        See :meth:`playable`.
        """
        if spotify.session_instance is None:
            raise RuntimeError('Session must be initialized')
        Error.maybe_raise(self.error)
        if not self.is_loaded:
            return None
        return bool(lib.sp_track_is_autolinked(
            spotify.session_instance.sp_session, self.sp_track))

    @property
    def playable(self):
        """The actual track that will be played when this track is played.

        See :meth:`is_autolinked`.
        """
        if spotify.session_instance is None:
            raise RuntimeError('Session must be initialized')
        Error.maybe_raise(self.error)
        # TODO What happens here if the track is unloaded?
        return Track(lib.sp_track_get_playable(
            spotify.session_instance.sp_session, self.sp_track))

    @property
    def is_placeholder(self):
        """Whether the track is a placeholder for a non-track object in the
        playlist.

        To convert to the real object::

            >>> track.is_placeholder
            True
            >>> track.link.type
            <LinkType.ARTIST: ...>
            >>> artist = track.link.as_artist()
        """
        Error.maybe_raise(self.error)
        # TODO What happens here if the track is unloaded?
        return bool(lib.sp_track_is_placeholder(self.sp_track))

    @property
    def is_starred(self):
        """Whether the track is starred by the current user.

        Will always return :class:`None` if the track isn't loaded.
        """
        if spotify.session_instance is None:
            raise RuntimeError('Session must be initialized')
        Error.maybe_raise(self.error)
        if not self.is_loaded:
            return None
        return bool(lib.sp_track_is_starred(
            spotify.session_instance.sp_session, self.sp_track))

    # TODO Add track.set_starred(True) and Track.set_starred(tracks, True)

    # TODO Add track.artists

    @property
    def album(self):
        """The album of the track.

        Will always return :class:`None` if the track isn't loaded.
        """
        Error.maybe_raise(self.error)
        sp_album = lib.sp_track_album(self.sp_track)
        return Album(sp_album) if sp_album else None

    @property
    def name(self):
        """The track's name.

        Will always return :class:`None` if the track isn't loaded.
        """
        Error.maybe_raise(self.error)
        name = to_unicode(lib.sp_track_name(self.sp_track))
        return name if name else None

    @property
    def duration(self):
        """The track's duration in milliseconds.

        Will always return :class:`None` if the track isn't loaded.
        """
        Error.maybe_raise(self.error)
        duration = lib.sp_track_duration(self.sp_track)
        return duration if duration else None

    @property
    def popularity(self):
        """The track's popularity in the range 0-100, 0 if undefined.

        Will always return :class:`None` if the track isn't loaded.
        """
        Error.maybe_raise(self.error)
        if not self.is_loaded:
            return None
        return lib.sp_track_popularity(self.sp_track)

    @property
    def disc(self):
        """The track's disc number. 1 or higher.

        Will always return :class:`None` if the track isn't part of an album or
        artist browser.
        """
        Error.maybe_raise(self.error)
        disc = lib.sp_track_disc(self.sp_track)
        return disc if disc else None

    @property
    def index(self):
        """The track's index number. 1 or higher.

        Will always return :class:`None` if the track isn't part of an album or
        artist browser.
        """
        Error.maybe_raise(self.error)
        index = lib.sp_track_index(self.sp_track)
        return index if index else None

    @property
    def link(self):
        """A :class:`Link` to the track."""
        from spotify.link import Link
        return Link(self, offset=0)

    def link_with_offset(self, offset):
        """A :class:`Link` to the track with an ``offset`` in milliseconds into
        the track."""
        from spotify.link import Link
        return Link(self, offset=offset)


class LocalTrack(Track):
    """A Spotify local track.

    TODO: Explain what a local track is. libspotify docs doesn't say much, but
    there are more details in Hallon's docs.
    """

    def __init__(self, artist=None, title=None, album=None, length=None):
        convert = lambda value: ffi.NULL if value is None else ffi.new(
            'char[]', to_bytes(value))

        artist = convert(artist)
        title = convert(title)
        album = convert(album)
        if length is None:
            length = -1

        sp_track = lib.sp_localtrack_create(artist, title, album, length)

        super(LocalTrack, self).__init__(sp_track, add_ref=False)


@make_enum('SP_TRACK_AVAILABILITY_')
class TrackAvailability(IntEnum):
    pass


@make_enum('SP_TRACK_OFFLINE_')
class TrackOfflineStatus(IntEnum):
    pass
