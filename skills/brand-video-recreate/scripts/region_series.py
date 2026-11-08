#!/usr/bin/env python3
"""프레임마다 한 영역의 값을 재서 표(CSV)로 만든다. 눈대중 대신 「프레임별 실측 표」를 쓰기 위한 도구.

사용: region_series.py <영상> --box x0,y0,x1,y1 [--color R,G,B] [--tol 40] [--out series.csv]
각 프레임에서:
  - mean_r,g,b : 영역 평균 색
  - luma       : 평균 밝기 (어두워짐·번쩍임 측정)
  - match      : --color 와 비슷한 픽셀 수 (글자가 뜨는 프레임, 빨강이 차오르는 양 등)
  - bbox       : 배경(첫 프레임)과 다른 픽셀의 바깥 상자 (물체의 위치·크기·낙하 속도)
읽는 법 예: match 가 처음 20%를 넘는 프레임 = 글자 등장 프레임.
           bbox 의 y 를 프레임마다 빼면 낙하 속도(픽셀/프레임 x fps = 픽셀/초).
필요: ffmpeg, numpy
"""
import argparse, csv, subprocess, sys
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video"); p.add_argument("--box", required=True)
    p.add_argument("--color"); p.add_argument("--tol", type=float, default=40)
    p.add_argument("--bgdiff", type=float, default=30, help="bbox 에서 배경과 다르다고 볼 밝기 차이")
    p.add_argument("--out")
    a = p.parse_args()
    x0, y0, x1, y1 = [int(v) for v in a.box.split(",")]
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height,r_frame_rate", "-of", "csv=p=0", a.video],
                        capture_output=True, text=True, check=True).stdout.strip().split(",")
    W, H = int(pr[0]), int(pr[1]); n, d = pr[2].split("/"); fps = float(n) / float(d)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vsync", "0", "-pix_fmt", "rgb24",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    size = W * H * 3
    col = np.array([int(v) for v in a.color.split(",")], np.float32) if a.color else None
    rows = []; bg = None; i = 0
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)[y0:y1, x0:x1].astype(np.float32)
        luma = fr @ np.array([0.299, 0.587, 0.114], np.float32)
        if bg is None:
            bg = luma.copy()
        mt = int((np.abs(fr - col).max(2) <= a.tol).sum()) if col is not None else ""
        ys, xs = np.where(np.abs(luma - bg) > a.bgdiff)
        bbox = (int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0) if len(xs) else ("", "", "", "")
        m = fr.reshape(-1, 3).mean(0)
        rows.append([i, round(i / fps, 4), *[round(float(v), 1) for v in m], round(float(luma.mean()), 1), mt, *bbox])
        i += 1
    head = ["frame", "t", "mean_r", "mean_g", "mean_b", "luma", "match", "bx0", "by0", "bx1", "by1"]
    f = open(a.out, "w", newline="") if a.out else sys.stdout
    w = csv.writer(f); w.writerow(head); w.writerows(rows)
    if a.out:
        f.close(); print(f"{len(rows)}프레임 -> {a.out}")


if __name__ == "__main__":
    main()
