import unittest

from matrix_deck import HEIGHT, PIXELS, WIDTH
from matrix_deck.protocol import (
    FWK_MAGIC,
    column_from_pixels,
    iter_grey_frame,
    pack_bw_frame,
    pack_grey_column,
    rotate180,
)


class ProtocolTests(unittest.TestCase):
    def test_grey_column_layout(self):
        col = list(range(HEIGHT))
        packet = pack_grey_column(3, col)
        self.assertEqual(packet[0], FWK_MAGIC[0])
        self.assertEqual(packet[1], FWK_MAGIC[1])
        self.assertEqual(packet[2], 0x07)
        self.assertEqual(packet[3], 3)
        self.assertEqual(list(packet[4:]), col)
        self.assertEqual(len(packet), 4 + HEIGHT)

    def test_grey_column_rejects_bad_shapes(self):
        with self.assertRaises(ValueError):
            pack_grey_column(0, [1, 2, 3])
        with self.assertRaises(ValueError):
            pack_grey_column(9, [0] * HEIGHT)

    def test_full_grey_frame_is_nine_columns_and_flush(self):
        pixels = [(i * 13) % 256 for i in range(PIXELS)]
        packets = iter_grey_frame(pixels)
        self.assertEqual(len(packets), WIDTH + 1)
        self.assertEqual(packets[-1], bytes((0x32, 0xAC, 0x08, 0x00)))
        for x, packet in enumerate(packets[:-1]):
            self.assertEqual(packet[3], x)
            self.assertEqual(list(packet[4:]), column_from_pixels(pixels, x))

    def test_bw_packing_matches_official_bit_order(self):
        pixels = [0] * PIXELS
        pixels[0] = 255
        pixels[8] = 200
        pixels[9] = 255  # (0, 1)
        packed = pack_bw_frame(pixels)
        self.assertEqual(packed[0:3], bytes((0x32, 0xAC, 0x06)))
        self.assertEqual(len(packed), 3 + 39)
        bits = packed[3:]
        self.assertTrue(bits[0] & (1 << 0))
        self.assertTrue(bits[1] & (1 << 0))  # index 8
        self.assertTrue(bits[1] & (1 << 1))  # index 9

    def test_rotate180_swaps_corners(self):
        pixels = bytearray(PIXELS)
        pixels[0] = 11  # top-left
        pixels[WIDTH - 1] = 22  # top-right
        pixels[(HEIGHT - 1) * WIDTH] = 33  # bottom-left
        pixels[-1] = 44  # bottom-right
        rotated = rotate180(pixels)
        self.assertEqual(rotated[0], 44)
        self.assertEqual(rotated[WIDTH - 1], 33)
        self.assertEqual(rotated[(HEIGHT - 1) * WIDTH], 22)
        self.assertEqual(rotated[-1], 11)
