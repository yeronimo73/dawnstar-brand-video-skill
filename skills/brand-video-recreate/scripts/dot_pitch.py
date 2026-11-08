#!/usr/bin/env python3
"""점무늬(망점)·줄무늬의 간격과 기울기 재기. 푸리에 변환에서 가장 센 반복 무늬를 찾는다.

사용: dot_pitch.py <이미지> [--box x0,y0,x1,y1] [--top 3]
예) 사진 없이 무늬만 보이는 바탕 한 곳을 --box 로 잘라 넣으면
    "간격 16.0px, 기울기 30도" 처럼 숫자가 나온다.
기울기는 무늬 파동 방향이 가로축과 이루는 각도(화면 좌표, 0~90도, 정사각 격자일 때). 대각선 봉우리(간격의 0.7배)는 같은 격자의 다른 방향이다.
주의: 사진·글자가 섞인 곳은 피하고 무늬만 있는 곳을 고른다. 박스는 256px 이상이 안정적이다.
필요: numpy, Pillow
"""
import argparse, math
import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image"); p.add_argument("--box"); p.add_argument("--top", type=int, default=3)
    a = p.parse_args()
    im = Image.open(a.image).convert("L")
    if a.box:
        x0, y0, x1, y1 = [int(v) for v in a.box.split(",")]
        im = im.crop((x0, y0, x1, y1))
    g = np.asarray(im, np.float32)
    g = g - g.mean()
    h, w = g.shape
    g = g * np.outer(np.hanning(h), np.hanning(w))
    # 0 채우기로 해상도를 올려 봉우리 위치를 곱게 읽는다
    S = 1 << int(math.ceil(math.log2(max(h, w) * 2)))
    F = np.abs(np.fft.fftshift(np.fft.fft2(g, s=(S, S))))
    cy = cx = S // 2
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(yy - cy, xx - cx)
    F[r < S / max(h, w) * 3] = 0          # 아주 느린 변화(밝기 얼룩)는 뺀다
    F[(xx < cx)] = 0                       # 대칭 반쪽만 본다
    F[(xx == cx) & (yy < cy)] = 0
    peaks = []
    Fw = F.copy()
    for _ in range(a.top):
        k = np.unravel_index(Fw.argmax(), Fw.shape)
        v = Fw[k]
        if v <= 0:
            break
        fy, fx = (k[0] - cy) / S, (k[1] - cx) / S     # 주파수 (주기/픽셀)
        fr = math.hypot(fx, fy)
        period = 1 / fr
        ang = math.degrees(math.atan2(fy, fx)) % 180  # 무늬 파동 방향 (화면 좌표: 오른쪽이 0도, 아래로 돌수록 커짐)
        peaks.append((v, period, ang))
        Fw[max(0, k[0] - 6): k[0] + 7, max(0, k[1] - 6): k[1] + 7] = 0
    if not peaks:
        raise SystemExit("반복 무늬를 찾지 못했습니다")
    top = peaks[0][0]
    for v, per, ang in peaks:
        print(f"세기 {v / top:4.2f}  간격 {per:6.2f}px  파동 방향 {ang:6.1f}도  (90도 나머지 {ang % 90:5.1f})")
    v, per, ang = peaks[0]
    print(f"=> 가장 센 무늬: 간격 약 {per:.1f}px, 기울기 약 {ang % 90:.0f}도 (정사각 격자 기준, 화면 좌표)")


if __name__ == "__main__":
    main()
