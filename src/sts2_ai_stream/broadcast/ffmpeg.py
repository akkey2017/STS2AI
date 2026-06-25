from __future__ import annotations


def build_ffmpeg_command(
    display: str,
    size: str,
    fps: int,
    rtmp_url: str,
    stream_key: str,
    encoder: str = "h264_nvenc",
    bitrate: str = "8000k",
) -> list[str]:
    target = f"{rtmp_url.rstrip('/')}/{stream_key}" if stream_key else rtmp_url
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-f",
        "x11grab",
        "-video_size",
        size,
        "-framerate",
        str(fps),
        "-i",
        display,
        "-c:v",
        encoder,
        "-b:v",
        bitrate,
        "-maxrate",
        bitrate,
        "-bufsize",
        str(int(bitrate.rstrip("k")) * 2) + "k" if bitrate.endswith("k") else bitrate,
        "-pix_fmt",
        "yuv420p",
        "-f",
        "flv",
        target,
    ]

