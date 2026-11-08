#!/usr/bin/env python3
"""접촉표: 프레임을 격자로 펼쳐 한 장에 놓는다. 장면 경계·움직임 장치를 눈으로 찾을 때 쓴다.

사용:
  contact_sheet.py <프레임 폴더|영상> <출력.jpg> [--every N] [--start 프레임] [--end 프레임]
                   [--cols 8] [--width 240] [--fps 30]
프레임 폴더는 extract_frames.sh 가 만든 0001.png 형식. 영상을 주면 임시로 전부 뽑는다.
각 칸 왼쪽 위에 프레임 번호(0부터)와 시각을 적는다.
"""
import argparse, glob, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("out")
    p.add_argument("--every", type=int, default=1, help="N프레임마다 한 칸")
    p.add_argument("--start", type=int, default=0); p.add_argument("--end", type=int, default=10**9)
    p.add_argument("--cols", type=int, default=8); p.add_argument("--width", type=int, default=240)
    p.add_argument("--fps", type=float, default=30.0, help="시각 표시에 쓸 fps (영상을 주면 자동)")
    a = p.parse_args()

    folder = a.src
    if os.path.isfile(a.src):
        folder = tempfile.mkdtemp(prefix="cs_")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-vsync", "0", f"{folder}/%04d.png"], check=True)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=r_frame_rate", "-of", "csv=p=0", a.src], capture_output=True, text=True).stdout.strip()
        n, d = r.split("/") if "/" in r else (r, "1")
        a.fps = float(n) / float(d)
    files = sorted(glob.glob(os.path.join(folder, "*.png")) + glob.glob(os.path.join(folder, "*.jpg")))
    if not files:
        sys.exit("프레임이 없습니다")
    idx = [i for i in range(len(files)) if a.start <= i <= a.end and (i - a.start) % a.every == 0]
    first = Image.open(files[0])
    tw = a.width; th = round(first.height * tw / first.width)
    rows = (len(idx) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * tw, rows * th), (20, 20, 20))
    for k, i in enumerate(idx):
        im = Image.open(files[i]).convert("RGB").resize((tw, th), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        label = f"{i}  {i / a.fps:.2f}s"
        d.rectangle([0, 0, 8 + 7 * len(label), 14], fill=(0, 0, 0))
        d.text((3, 1), label, fill=(255, 255, 0))
        sheet.paste(im, ((k % a.cols) * tw, (k // a.cols) * th))
    sheet.save(a.out, quality=88)
    print(f"{len(idx)}칸, {a.cols}열 x {rows}행 -> {a.out}  ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
