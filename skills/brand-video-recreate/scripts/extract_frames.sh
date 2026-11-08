#!/usr/bin/env bash
# 영상에서 프레임을 뽑는다.
# 사용: extract_frames.sh <영상> <출력폴더> [all|숫자] [png|jpg]
#   all   = 원본 프레임 전부 (기본). 원본 fps 그대로, 건너뛰지 않는다.
#   숫자  = 1초에 그 숫자만큼 (예: 4 -> 초당 4장)
# 파일 이름은 0001부터 (프레임 f 는 f+1 번 파일). 원본 크기·화질 그대로.
set -euo pipefail
in="${1:?사용: extract_frames.sh <영상> <출력폴더> [all|숫자] [png|jpg]}"
out="${2:?출력 폴더가 필요합니다}"
mode="${3:-all}"
fmt="${4:-png}"
mkdir -p "$out"
if [ "$fmt" = "jpg" ]; then q="-q:v 2"; ext=jpg; else q=""; ext=png; fi
if [ "$mode" = "all" ]; then
  ffmpeg -v error -y -i "$in" -vsync 0 $q "$out/%04d.$ext"
else
  ffmpeg -v error -y -i "$in" -vf "fps=$mode" $q "$out/%04d.$ext"
fi
n=$(ls "$out" | grep -c "\.$ext$" || true)
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$in")
echo "프레임 $n 장 -> $out (원본 fps $fps, 모드 $mode)"
