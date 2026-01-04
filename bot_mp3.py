import asyncio
import logging
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from yt_dlp import YoutubeDL


BOT_TOKEN = ""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("mp3bot")

bot = AsyncTeleBot(BOT_TOKEN)

YOUTUBE_HOST_RE = re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE)
MAX_TITLE_LEN = 64
MAX_CALLBACK_URL_LEN = 170
AUDIO_BITRATE = "192"

DOWNLOAD_WORKERS = 3
download_sem = asyncio.Semaphore(DOWNLOAD_WORKERS)

waiting_for_url: dict[int, bool] = {}


@dataclass(frozen=True)
class VideoMeta:
    url: str
    title: str
    duration_str: str
    duration_sec: int
    thumbnail: Optional[str]
    uploader: Optional[str]


def looks_like_youtube_url(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if len(t) < 10:
        return False
    return bool(YOUTUBE_HOST_RE.search(t))


def fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "Unknown"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def home_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("Download MP3", callback_data="start_dl"))
    kb.row(types.InlineKeyboardButton("Help", callback_data="help"))
    return kb


def build_keyboard_for_url(url: str) -> types.InlineKeyboardMarkup:
    safe_url = url.strip()
    if len(safe_url) > MAX_CALLBACK_URL_LEN:
        safe_url = safe_url[:MAX_CALLBACK_URL_LEN]

    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("Download MP3", callback_data=f"dl|{safe_url}"))
    kb.row(types.InlineKeyboardButton("Help", callback_data="help"))
    return kb


def card_text(meta: VideoMeta) -> str:
    uploader_line = f"\nUploader: {meta.uploader}" if meta.uploader else ""
    return f"Title: {meta.title}\nDuration: {meta.duration_str}{uploader_line}"


def _extract_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download_mp3(url: str, out_dir: str) -> Path:
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(out_dir_path / "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": AUDIO_BITRATE,
            }
        ],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        vid = info.get("id") or "audio"
        mp3_path = out_dir_path / f"{vid}.mp3"

    if mp3_path.exists():
        return mp3_path

    mp3s = list(out_dir_path.glob("*.mp3"))
    if mp3s:
        return mp3s[0]

    raise FileNotFoundError("MP3 output not found after download")


async def get_video_meta(url: str) -> Optional[VideoMeta]:
    try:
        info = await asyncio.to_thread(_extract_info, url)
        title = info.get("title") or "Unknown Title"
        duration_sec = int(info.get("duration") or 0)
        thumb = info.get("thumbnail")
        uploader = info.get("uploader") or info.get("channel")
        return VideoMeta(
            url=url,
            title=title,
            duration_str=fmt_duration(duration_sec),
            duration_sec=duration_sec,
            thumbnail=thumb,
            uploader=uploader,
        )
    except Exception as e:
        log.warning("extract_info failed: %s", e, exc_info=False)
        return None


async def download_mp3_file(url: str) -> tuple[Path, Path]:
    tmp_dir = Path(tempfile.mkdtemp(prefix="ytmp3_"))
    try:
        mp3_path = await asyncio.to_thread(_download_mp3, url, str(tmp_dir))
        return mp3_path, tmp_dir
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


async def send_preview_reply(chat_id: int, reply_to_message_id: int, url: str) -> None:
    processing = await bot.send_message(
        chat_id,
        "Analyzing URL…",
        reply_to_message_id=reply_to_message_id,
    )

    meta = await get_video_meta(url)
    if not meta:
        await bot.edit_message_text(
            "Video info read kora jay nai. Onno link try koro.",
            chat_id=chat_id,
            message_id=processing.message_id,
        )
        return

    kb = build_keyboard_for_url(meta.url)
    caption = card_text(meta)

    try:
        if meta.thumbnail:
            await bot.send_photo(
                chat_id,
                photo=meta.thumbnail,
                caption=caption,
                reply_markup=kb,
                reply_to_message_id=reply_to_message_id,
            )
        else:
            await bot.send_message(
                chat_id,
                caption,
                reply_markup=kb,
                reply_to_message_id=reply_to_message_id,
            )
        await bot.delete_message(chat_id, processing.message_id)
    except Exception:
        await bot.edit_message_text(
            caption,
            chat_id=chat_id,
            message_id=processing.message_id,
            reply_markup=kb,
        )


@bot.message_handler(commands=["start"])
async def start_cmd(message):
    waiting_for_url.pop(message.from_user.id, None)
    text = (
        "YouTube MP3 Downloader\n\n"
        "Group: /download_mp3 <url>\n"
        "Private: Tap Download MP3, then send URL"
    )
    await bot.send_message(message.chat.id, text, reply_markup=home_keyboard())


@bot.message_handler(commands=["download_mp3"])
async def download_cmd(message):
    parts = (message.text or "").split(maxsplit=1)
    url = parts[1].strip() if len(parts) > 1 else ""

    if not looks_like_youtube_url(url):
        await bot.send_message(
            message.chat.id,
            "Use: /download_mp3 <youtube_url>",
            reply_to_message_id=message.message_id,
        )
        return

    await send_preview_reply(
        chat_id=message.chat.id,
        reply_to_message_id=message.message_id,
        url=url,
    )


@bot.callback_query_handler(func=lambda c: c.data == "help")
async def cb_help(call):
    waiting_for_url.pop(call.from_user.id, None)
    txt = (
        "How to use\n\n"
        "Group:\n"
        "/download_mp3 https://youtu.be/xxxx\n\n"
        "Private:\n"
        "1) Tap Download MP3\n"
        "2) Send YouTube URL\n\n"
        "Then press Download MP3 button."
    )
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, txt, reply_markup=home_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "start_dl")
async def cb_start_dl(call):
    waiting_for_url[call.from_user.id] = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, "Send a YouTube URL now.")


@bot.message_handler(func=lambda m: True, content_types=["text"])
async def handle_text(message):
    text = (message.text or "").strip()
    if waiting_for_url.get(message.from_user.id):
        if not looks_like_youtube_url(text):
            await bot.send_message(message.chat.id, "Valid YouTube URL send koro.")
            return
        waiting_for_url.pop(message.from_user.id, None)
        await send_preview_reply(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            url=text,
        )
        return

    if message.chat.type == "private" and looks_like_youtube_url(text):
        await send_preview_reply(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            url=text,
        )
        return

    if message.chat.type in ("group", "supergroup"):
        return

    await bot.send_message(message.chat.id, "Tap Download MP3.", reply_markup=home_keyboard())


@bot.callback_query_handler(func=lambda c: c.data.startswith("dl|"))
async def cb_download(call):
    url = call.data.split("|", 1)[1].strip()
    if not looks_like_youtube_url(url):
        await bot.answer_callback_query(call.id, "Invalid URL.", show_alert=True)
        return

    await bot.answer_callback_query(call.id, "Starting…")
    status = await bot.send_message(call.message.chat.id, "Downloading…")

    async with download_sem:
        tmp_root: Optional[Path] = None
        try:
            mp3_path, tmp_root = await download_mp3_file(url)
            meta = await get_video_meta(url)
            title = (meta.title if meta else "MP3")[:MAX_TITLE_LEN]
            duration = meta.duration_str if meta else "Unknown"

            caption = f"Title: {title}\nDuration: {duration}"

            with open(mp3_path, "rb") as f:
                await bot.send_audio(
                    call.message.chat.id,
                    audio=f,
                    title=title,
                    caption=caption,
                )

            await bot.delete_message(call.message.chat.id, status.message_id)

        except Exception as e:
            log.exception("download failed")
            await bot.edit_message_text(
                f"Download failed: {type(e).__name__}",
                chat_id=call.message.chat.id,
                message_id=status.message_id,
            )
        finally:
            if tmp_root:
                shutil.rmtree(tmp_root, ignore_errors=True)


async def main():
    log.info("Bot running…")
    await bot.infinity_polling(timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
