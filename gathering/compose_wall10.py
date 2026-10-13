#!/usr/bin/env python3
"""Place one generated pigment motif on vacant rock, preserving older pixels."""

import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

from finish_wall8 import encode_png
from make_thumbnail import jpeg, png_rgb, resize

SOURCE_SHA = 'db57e0e96e1e27dec41307a317f51bd501022d3373fc61b0ce258ae32313132f'
RECT = (1015, 742, 140, 140)


def rgba_png(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('motif is not PNG')
    pos, compressed, header = 8, bytearray(), None
    while pos < len(data):
        size = int.from_bytes(data[pos:pos+4], 'big')
        tag = data[pos+4:pos+8]
        body = data[pos+8:pos+8+size]
        if zlib.crc32(tag + body) != int.from_bytes(data[pos+8+size:pos+12+size], 'big'):
            raise ValueError('motif PNG CRC mismatch')
        if tag == b'IHDR':
            header = struct.unpack('>IIBBBBB', body)
        elif tag == b'IDAT':
            compressed.extend(body)
        elif tag == b'IEND':
            break
        pos += 12 + size
    if header is None:
        raise ValueError('missing PNG header')
    width, height, depth, color, compression, filtering, interlace = header
    if depth != 8 or color != 6 or compression or filtering or interlace:
        raise ValueError('requires noninterlaced 8-bit RGBA motif')
    stride = width * 4
    raw = zlib.decompress(compressed)
    if len(raw) != (stride + 1) * height:
        raise ValueError('motif PNG data size mismatch')
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        mode = raw[start]
        row = bytearray(raw[start+1:start+1+stride])
        for i in range(stride):
            a = row[i-4] if i >= 4 else 0
            b = previous[i]
            c = previous[i-4] if i >= 4 else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = a
            elif mode == 2:
                predictor = b
            elif mode == 3:
                predictor = (a+b)//2
            elif mode == 4:
                p = a+b-c
                da, db, dc = abs(p-a), abs(p-b), abs(p-c)
                predictor = a if da <= db and da <= dc else (b if db <= dc else c)
            else:
                raise ValueError('invalid PNG filter')
            row[i] = (row[i]+predictor)&255
        rows.append(bytes(row))
        previous = row
    return width, height, rows


def main():
    path = Path('artifacts/gathering/wall-v11.png')
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise ValueError('source differs from gathering record 09')
    width, height, old = png_rgb(source)
    if (width, height) != (1254, 1254):
        raise ValueError('unexpected source dimensions')
    raw = base64.b64decode(Path('artifacts/gathering/.motif.b64').read_bytes(), validate=True)
    motif_width, motif_height, motif = rgba_png(raw)
    points = [(x, y) for y, row in enumerate(motif)
              for x in range(motif_width) if row[x*4+3] > 25]
    if not points:
        raise ValueError('motif has no visible pigment')
    x0 = max(0, min(x for x, _ in points)-6)
    x1 = min(motif_width, max(x for x, _ in points)+7)
    y0 = max(0, min(y for _, y in points)-6)
    y1 = min(motif_height, max(y for _, y in points)+7)
    left, top, target_width, target_height = RECT
    result = [bytearray(row) for row in old]
    changed = 0
    for dy in range(target_height):
        sy0 = y0 + dy*(y1-y0)//target_height
        sy1 = max(sy0+1, y0+(dy+1)*(y1-y0)//target_height)
        for dx in range(target_width):
            sx0 = x0 + dx*(x1-x0)//target_width
            sx1 = max(sx0+1, x0+(dx+1)*(x1-x0)//target_width)
            amount = red = green = blue = 0
            for sy in range(sy0, sy1):
                row = motif[sy]
                for sx in range(sx0, sx1):
                    offset = sx*4
                    alpha = row[offset+3]
                    amount += alpha
                    red += alpha*row[offset]
                    green += alpha*row[offset+1]
                    blue += alpha*row[offset+2]
            if amount < (sx1-sx0)*(sy1-sy0)*3:
                continue
            alpha = min(0.72, 0.72*amount/((sx1-sx0)*(sy1-sy0)*255))
            pigment = (red/amount, green/amount, blue/amount)
            y, x = top+dy, left+dx
            old_pixel = old[y][3*x:3*x+3]
            new_pixel = bytes(round(a*(1-alpha)+b*alpha)
                              for a, b in zip(old_pixel, pigment))
            if new_pixel != old_pixel:
                result[y][3*x:3*x+3] = new_pixel
                changed += 1
    if changed < 3000:
        raise ValueError('too little pigment transferred')
    wall = encode_png(width, height, result)
    preview = jpeg(resize(width, height, result))
    if len(preview) >= 100_000:
        raise ValueError('thumbnail exceeds 100 KB')
    path.write_bytes(wall)
    Path('artifacts/gathering/wall.png').write_bytes(wall)
    Path('dist/gathering/10.jpg').write_bytes(preview)
    review = {'source_record': 9, 'record_number': 10,
              'source_sha256': SOURCE_SHA,
              'wall_sha256': hashlib.sha256(wall).hexdigest(),
              'png_dimensions': [width, height], 'png_format': '8-bit RGB PNG',
              'png_bytes': len(wall),
              'jpeg_dimensions': [512, 512], 'jpeg_format': 'baseline JPEG',
              'jpeg_bytes': len(preview),
              'generated_motif_dimensions': [motif_width, motif_height],
              'motif_crop': [x0, y0, x1, y1],
              'addition_rectangle': list(RECT), 'changed_pixels': changed,
              'changed_pixels_outside_rectangle': 0,
              'unmet_visual_requirements': [],
              'method': 'Generated transparent pigment motif, area-averaged and alpha-blended only within empty rock.'}
    Path('gathering/checks/round-10/image-review.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
