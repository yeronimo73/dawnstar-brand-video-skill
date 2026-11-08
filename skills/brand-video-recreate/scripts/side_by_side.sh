#!/usr/bin/env bash
# 원본 | 재현 나란히 영상 만들기 (왼쪽 원본, 오른쪽 재현).
# 사용: side_by_side.sh <원본> <재현> <출력.mp4> [높이=960] [orig|none]
#   마지막 인자 orig 이면 원본 소리를 넣는다 (내부 검토용). 기본은 소리 없음.
set -euo pipefail
a="${1:?원본 영상}"; b="${2:?재현 영상}"; out="${3:?출력 파일}"
h="${4:-960}"; aud="${5:-none}"
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$a")
fc="[0:v]fps=$fps,scale=-2:$h,setsar=1[l];[1:v]fps=$fps,scale=-2:$h,setsar=1[r];[l][r]hstack=inputs=2:shortest=1[v]"
if [ "$aud" = "orig" ]; then
  ffmpeg -v error -y -i "$a" -i "$b" -filter_complex "$fc" -map "[v]" -map 0:a? -c:v libx264 -crf 18 -pix_fmt yuv420p -shortest "$out"
else
  ffmpeg -v error -y -i "$a" -i "$b" -filter_complex "$fc" -map "[v]" -an -c:v libx264 -crf 18 -pix_fmt yuv420p "$out"
fi
echo "만듦: $out"
