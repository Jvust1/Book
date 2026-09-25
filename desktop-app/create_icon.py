from pathlib import Path
import sys

from PIL import Image, ImageDraw


target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((16, 16, 240, 240), radius=54, fill="#32624e")
draw.line((57, 76, 57, 187), fill="#fffdf6", width=10)
draw.line((199, 76, 199, 187), fill="#fffdf6", width=10)
draw.arc((57, 49, 128, 101), 180, 355, fill="#fffdf6", width=10)
draw.arc((128, 49, 199, 101), 185, 360, fill="#fffdf6", width=10)
draw.line((128, 72, 128, 184), fill="#fffdf6", width=8)
draw.arc((57, 158, 128, 210), 185, 360, fill="#fffdf6", width=10)
draw.arc((128, 158, 199, 210), 180, 355, fill="#fffdf6", width=10)
image.save(target, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
