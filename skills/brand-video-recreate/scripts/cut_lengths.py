#!/usr/bin/env python3
"""컷 감지: 장면이 바뀌는 프레임을 찾아 컷 수와 컷 길이(중간값·평균·분포)를 잰다.

사용: cut_lengths.py <영상> [--thr 0.12] [--json out.json]
방법: 영상을 작은 회색 화면(96px 폭)으로 풀어, 이웃 프레임의 평균 절대 차이(0~1)가
      --thr 를 넘으면 컷. 같은 장면 안의 빠른 움직임이 컷으로 잡히면 --thr 을 올리고,
      부드러운 전환(디졸브)을 놓치면 내린다. 결과 표를 접촉표와 맞춰 보고 확정한다.
필요: ffmpeg, numpy
"""
import argparse, json, statistics, subprocess
import numpy as np


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True).stdout.strip().split(",")
    n, d = r[2].split("/")
    return int(r[0]), int(r[1]), float(n) / float(d)


def gray_frames(path, w=96):
    W, H, fps = probe(path)
    h = max(2, round(H * w / W / 2) * 2)
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vsync", "0", "-vf", f"scale={w}:{h}:flags=area",
           "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h
    while True:
        buf = pr.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).astype(np.float32) / 255.0
    pr.wait()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video"); p.add_argument("--thr", type=float, default=0.12)
    p.add_argument("--json")
    a = p.parse_args()
    _, _, fps = probe(a.video)
    prev = None; diffs = []; n = 0
    for fr in gray_frames(a.video):
        if prev is not None:
            diffs.append(float(np.abs(fr - prev).mean()))
        prev = fr; n += 1
    cuts = [i + 1 for i, d in enumerate(diffs) if d > a.thr]   # 컷 뒤 첫 프레임 번호(0부터)
    starts = [0] + cuts; ends = cuts + [n]
    lens = [(e - s) / fps for s, e in zip(starts, ends)]
    out = {
        "frames": n, "fps": round(fps, 3), "duration": round(n / fps, 3), "threshold": a.thr,
        "segments": len(lens), "median_s": round(statistics.median(lens), 3),
        "mean_s": round(statistics.mean(lens), 3), "min_s": round(min(lens), 3), "max_s": round(max(lens), 3),
        "under_0.5s": sum(l < 0.5 for l in lens), "0.5-2s": sum(0.5 <= l < 2 for l in lens),
        "2-4s": sum(2 <= l < 4 for l in lens), "over_4s": sum(l >= 4 for l in lens),
        "cut_frames": cuts, "lengths_s": [round(l, 3) for l in lens],
    }
    print(f"프레임 {n}장, {fps:.2f}fps, {n / fps:.2f}초")
    print(f"컷(장면) {out['segments']}개  중간값 {out['median_s']}초  평균 {out['mean_s']}초  최소 {out['min_s']}  최대 {out['max_s']}")
    print(f"분포: 0.5초 미만 {out['under_0.5s']} / 0.5~2초 {out['0.5-2s']} / 2~4초 {out['2-4s']} / 4초 이상 {out['over_4s']}")
    print("컷 시작 프레임:", cuts[:60], "..." if len(cuts) > 60 else "")
    if a.json:
        json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
        print("저장:", a.json)


if __name__ == "__main__":
    main()
