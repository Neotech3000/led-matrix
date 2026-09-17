"""Framework Laptop 16 LED Matrix serial protocol.

The modules speak USB CDC-ACM at 115200 baud. Every command starts with
the magic bytes 0x32 0xAC (Framework's USB vendor ID).

Each matrix is 9 columns by 34 rows of white LEDs with 8-bit PWM.
"""

from __future__ import annotations

from matrix_deck import HEIGHT, WIDTH

FWK_MAGIC = (0x32, 0xAC)
FWK_VID = 0x32AC
LED_MATRIX_PID = 0x0020

CMD_BRIGHTNESS = 0x00
CMD_SLEEP = 0x03
CMD_DRAW_BW = 0x06
CMD_STAGE_GREY_COL = 0x07
CMD_FLUSH_COLS = 0x08
CMD_VERSION = 0x20


def _cmd(command: int, *params: int) -> bytes:
    return bytes((FWK_MAGIC[0], FWK_MAGIC[1], command, *params))


def pack_sleep(sleeping: bool) -> bytes:
    return _cmd(CMD_SLEEP, 1 if sleeping else 0)


def pack_brightness(value: int) -> bytes:
    return _cmd(CMD_BRIGHTNESS, max(0, min(255, int(value))))


def pack_version_query() -> bytes:
    return _cmd(CMD_VERSION)


def pack_grey_column(column: int, values) -> bytes:
    """Stage one 34-pixel greyscale column. Must be followed by flush."""
    if not 0 <= column < WIDTH:
        raise ValueError(f"column {column} out of range")
    if len(values) != HEIGHT:
        raise ValueError(f"column needs {HEIGHT} values, got {len(values)}")
    body = [max(0, min(255, int(v))) for v in values]
    return _cmd(CMD_STAGE_GREY_COL, column, *body)


def pack_flush() -> bytes:
    return _cmd(CMD_FLUSH_COLS, 0x00)


def pack_bw_frame(pixels) -> bytes:
    """Pack a 9x34 buffer into the 39-byte DrawBW bitmap (row-major bits)."""
    if len(pixels) != WIDTH * HEIGHT:
        raise ValueError("expected 306 pixels")
    vals = [0] * 39
    for i, value in enumerate(pixels):
        if value > 127:
            vals[i // 8] |= 1 << (i % 8)
    return _cmd(CMD_DRAW_BW, *vals)


def column_from_pixels(pixels, column: int) -> list[int]:
    """Extract a vertical slice (34 values) from a row-major 9x34 buffer."""
    return [pixels[row * WIDTH + column] & 0xFF for row in range(HEIGHT)]


def iter_grey_frame(pixels) -> list[bytes]:
    """All serial packets needed to draw one greyscale frame."""
    packets = [pack_grey_column(x, column_from_pixels(pixels, x)) for x in range(WIDTH)]
    packets.append(pack_flush())
    return packets


def rotate180(pixels: bytes | bytearray | list[int]) -> bytearray:
    """Rotate a 9x34 buffer 180°, for a module installed the other way up."""
    out = bytearray(WIDTH * HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            out[(HEIGHT - 1 - y) * WIDTH + (WIDTH - 1 - x)] = pixels[y * WIDTH + x]
    return out


def maybe_orient(pixels, flip: bool):
    return rotate180(pixels) if flip else pixels
