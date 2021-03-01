from argparse import ArgumentParser

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
_font_file = "{}.bin"
_char_set = [{}]
_char_end = [{}]

width = {}
height = {}

with open(_font_file, 'rb') as f:
    _font_bin = f.read()

def get_ch(ch):
    if ch not in _char_set:
        ch = "?"
    i = _char_set.index(ch)
    start = _char_end[i-1] if i > 0 else 0
    end = _char_end[i]
    return _font_bin[start:end]
'''


if __name__ == '__main__':
    parser = ArgumentParser(description='')
    parser.add_argument('infile', type=str, help='Input file path')
    parser.add_argument('height', type=int, help='Font height in pixels')
    parser.add_argument('charset', type=str, help='Character set. e.g. 1234567890: to restrict for a clock display.')
    parser.add_argument('outfile', type=str, help='Path and name of output files, {{.bin,.py}} is appended')
    args = parser.parse_args()

    fnt = Font(args.infile, args.height, MINCHAR, MAXCHAR, True, 63, args.charset, False)

    with open(args.outfile + '.bin', 'wb') as f:
        char_set = []
        char_end = []
        for char, char_params in fnt.items():
            char_set.append(char)
            bitmap = char_params[0]
            f.write(bytes(bitmap.get_hybrid()))
            char_end.append(f.tell())
    with open(args.outfile + '.py', 'wt') as f:
        f.write(OUT.format(args.outfile,
                           ', '.join([f'"{c}"' for c in char_set]),
                           ', '.join([str(i) for i in char_end]),
                           fnt.width, fnt.height))
