# TOOLS/youtube.md

YouTube Data API access for Jeff's channels.

## Channels

| Channel | ID | Handle | Subs |
|---|---|---|---|
| **TrustOffice** | `UCDy6M-wAxXWxhgTZhSdZ4RA` | `@trustofficeapp` | 13 |

Same Google account (`jeff@socialize.video`), accessible via the OAuth token.

## Full access token (includes YouTube)

- **Path:** `~/.hermes/google_token.json` (updated with YouTube scopes)
- **Scopes:** `youtube.readonly`, `youtube.upload` + all Workspace scopes
- **Use for:** Upload, metadata, transcripts, comments, thumbnails, playlists, analytics

## Quick access token

- **Path:** `~/.hermes/secrets/google_ai_youtube.env` (`YOUTUBE_ACCESS_TOKEN`, `YOUTUBE_REFRESH_TOKEN`)
- **Use for:** One-off curl/script calls needing just YouTube

## Known limitation

`mine=true` only returns whichever channel is "active" in the account switcher. Use channel ID directly (`?id=UC...`) for the other channel.

## Capabilities

- Upload videos to TrustOffice channel
- Download transcripts for blog/social repurposing
- Update descriptions, tags, playlists
- Read and respond to comments
- Pull channel stats (subscribers, views)