from argparse import ArgumentParser
import os
import sys

from font_to_py import MINCHAR, MAXCHAR
from font_to_py import Bitmap as BitmapBase
from font_to_py import Font as FontBase

class Bitmap(BitmapBase):
    def __init__(self, base):
        super().__init__(base.width, base.height, base.pixels)

    def get_hybrid(self):
        """
            │ MSB │ MSB │  │ MSB │
            │  :  │  :  │··│  :  │ ─┐
            │ LSB │ LSB │  │ LSB │  │
        ┌───────────────────────────┘
        │   │ MSB │ MSB │
        └─> │  :  │  :  │··
            │ LSB │ LSB │
        """
        for row in range(0, self.height, 8):
            for col in range(self.width):
                byte = 0x00
                for i in range(8):
                    if row + i >= self.height:
                        break
                    byte |= self.pixels[(row+i) * self.width + col] << (7 - i)
                yield 0xff ^ byte

class Font(FontBase):
    def _assign_values(self):
        super()._assign_values()
        for k, v in self.items():
            self[k] = [Bitmap(v[0])] + v[1:]


OUT = '''\
_char_set = {char_set}

height = {font_height}

with open("{font_bin}.bin", "rb") as f:
    _font_bin = f.read()

def get_ch(ch):
    c = _char_set.get(ch, _char_set["?"])
    return (_font_bin[c[0]:c[1]], c[2])

def str_width(s):
    w = 0
    for c in s:
        w += _char_set.get(c, _char_set["?"])[2]
    return w
'''


if __name__ == '__main__':
    parser = ArgumentParser(description='')
    parser.add_argument('infile', type=str, help='Input file path')
    parser.add_argument('height', type=int, help='Font height in pixels')
    parser.add_argument('charset', type=str, help='Character set. e.g. 1234567890: to restrict for a clock display.')
    parser.add_argument('outfile', type=str, help='Path and name of output files, {{.bin,.py}} is appended')
    args = parser.parse_args()

    fnt = Font(args.infile, args.height, MINCHAR, MAXCHAR, False, 63, args.charset, False)

    with open(args.outfile + '.bin', 'wb') as f:
        char_set = {}
        for char, char_params in fnt.items():
            start = f.tell()
            bmp = char_params[0]
            f.write(bytes(bmp.get_hybrid()))
            char_set[char] = (start, f.tell(), bmp.width)
    with open(args.outfile + '.py', 'wt') as f:
        f.write('# ' + ' '.join(sys.argv) + '\n')
        f.write(OUT.format(char_set=char_set,
                           font_height=fnt.height,
                           font_bin=os.path.basename(args.outfile)))
