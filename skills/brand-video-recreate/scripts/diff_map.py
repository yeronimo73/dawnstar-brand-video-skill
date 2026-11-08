#!/usr/bin/env python3
"""차이 지도: 원본 영상과 재현 영상을 프레임별로 겹쳐 얼마나 다른지 잰다.

사용:
  diff_map.py <원본> <재현> [--width 270] [--grid 6x8] [--heat-dir 폴더] [--heat-top 12]
              [--ranges 0-4.8,4.8-33.8] [--json out.json]
출력:
  - 전체 평균 차이 (0~255 밝기 단위. 5 아래면 눈으로 거의 구분이 안 된다)
  - 프레임별 점수에서 제일 다른 프레임 15개
  - 화면을 격자로 나눈 구역별 평균 -> 제일 다른 구역부터 고친다
  - --ranges 를 주면 구간(초)별 평균
  - --heat-dir 를 주면 가장 다른 프레임 N장의 히트맵(차이를 색으로 칠한 PNG: 원본 | 재현 | 차이)
두 영상은 같은 fps 로 맞춰 비교한다(원본 fps 기준). 더 짧은 쪽 길이까지만 비교.
필요: ffmpeg, numpy, Pillow
"""
import argparse, json, os, subprocess
import numpy as np
from PIL import Image


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True).stdout.strip().split(",")
    n, d = r[2].split("/")
    return int(r[0]), int(r[1]), float(n) / float(d)


def frames(path, w, h, fps):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h}:flags=area",
           "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h * 3
    while True:
        buf = pr.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    pr.wait()


def jet(x):
    """0~1 -> 파랑-초록-노랑-빨강"""
    x = np.clip(x, 0, 1)
    r = np.clip(1.5 - np.abs(4 * x - 3), 0, 1); g = np.clip(1.5 - np.abs(4 * x - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * x - 1), 0, 1)
    return (np.stack([r, g, b], -1) * 255).astype(np.uint8)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("orig"); p.add_argument("recreated")
    p.add_argument("--width", type=int, default=270); p.add_argument("--grid", default="6x8")
    p.add_argument("--heat-dir"); p.add_argument("--heat-top", type=int, default=12)
    p.add_argument("--ranges"); p.add_argument("--json")
    a = p.parse_args()
    W0, H0, fps = probe(a.orig)
    w = a.width; h = round(H0 * w / W0 / 2) * 2
    gx, gy = [int(v) for v in a.grid.split("x")]
    acc = np.zeros((gy, gx)); per = []; keep = {}
    for i, (fa, fb) in enumerate(zip(frames(a.orig, w, h, fps), frames(a.recreated, w, h, fps))):
        d = np.abs(fa.astype(np.float32) - fb.astype(np.float32)).mean(2)
        # 구역 평균 (가장자리 남는 픽셀은 버림)
        hh, ww = (h // gy) * gy, (w // gx) * gx
        g = d[:hh, :ww].reshape(gy, hh // gy, gx, ww // gx).mean((1, 3))
        acc += g
        per.append(float(d.mean()))
        if a.heat_dir:
            keep[i] = (fa.copy(), fb.copy(), d.copy())
            if len(keep) > 4000:
                keep.pop(min(keep, key=lambda k: per[k]))
    n = len(per)
    if n == 0:
        raise SystemExit("비교할 프레임이 없습니다")
    arr = np.array(per)
    print(f"비교 프레임 {n}장 ({n / fps:.2f}초, {fps:.2f}fps, {w}x{h}로 줄여 비교)")
    print(f"전체 평균 차이 {arr.mean():.2f} / 255   (중앙값 {np.median(arr):.2f}, 최대 {arr.max():.2f} @프레임 {int(arr.argmax())})")
    order = np.argsort(-arr)[:15]
    print("제일 다른 프레임:", ", ".join(f"{int(i)}({arr[i]:.1f})" for i in order))
    print(f"구역별 평균 (행 {gy} x 열 {gx}, 위-왼쪽이 첫 칸):")
    m = acc / n
    for row in m:
        print("  " + " ".join(f"{v:5.1f}" for v in row))
    k = np.unravel_index(m.argmax(), m.shape)
    print(f"제일 다른 구역: 행 {k[0]} 열 {k[1]} ({m.max():.1f})  <- 여기부터 고친다")
    res = {"frames": n, "fps": fps, "mean": float(arr.mean()), "median": float(np.median(arr)),
           "worst_frames": [int(i) for i in order], "grid_mean": m.round(2).tolist(), "ranges": {}}
    if a.ranges:
        print("구간별 평균:")
        for r in a.ranges.split(","):
            s, e = [float(v) for v in r.split("-")]
            seg = arr[int(s * fps): max(int(e * fps), int(s * fps) + 1)]
            if len(seg):
                print(f"  {s:g}~{e:g}초  평균 {seg.mean():.2f}  최대 {seg.max():.2f}")
                res["ranges"][r] = round(float(seg.mean()), 3)
    if a.heat_dir:
        os.makedirs(a.heat_dir, exist_ok=True)
        top = [int(i) for i in np.argsort(-arr)[: a.heat_top] if int(i) in keep]
        for i in top:
            fa, fb, d = keep[i]
            heat = jet(d / max(1.0, d.max() if d.max() > 30 else 30))
            Image.fromarray(np.hstack([fa, fb, heat])).save(f"{a.heat_dir}/heat_{i:04d}.png")
        print(f"히트맵 {len(top)}장 -> {a.heat_dir}  (왼쪽 원본 | 가운데 재현 | 오른쪽 차이)")
    if a.json:
        res["per_frame"] = [round(v, 3) for v in per]
        json.dump(res, open(a.json, "w"), indent=1)
        print("저장:", a.json)


if __name__ == "__main__":
    main()
