# dawnstar-brand-video-skill

잘 된 영상을 숫자로 뜯어서, 내 브랜드 영상으로 바꾸는 다섯 단계를 클로드(Claude Code)에게 그대로 시키는 스킬입니다.

유튜브 던스타 채널 영상 「당신의 영상이 절대 딸깍으로 안 되는 이유」에서 약속드린 무료 자료입니다. 영상에서 쓴 지시문, 영상별 작업 순서, 캐릭터 목 움직임 계산도 같은 저장소에 있습니다.

## 왜 필요한가

AI에게 "이 영상처럼 멋지게 만들어 줘"라고 하면 비슷하긴 한데 뭔가 다른 영상이 나옵니다. 컷 하나가 몇 초인지, 글자가 몇 번째 프레임에 뜨는지, 물체가 얼마나 빨리 떨어지는지는 눈으로 안 보입니다. 하지만 전부 숫자라서, 재서 건네면 AI가 그대로 만들 수 있습니다.

## 다섯 단계

1. 내 브랜드에 맞는 잘 된 영상을 하나 고릅니다. 원본 화질로 받아 둡니다. 화질이 낮으면 작은 움직임을 놓칩니다.
2. 숫자로 뜯습니다. 프레임을 전부 뽑아 펼치고, 위치·크기·속도·색을 잽니다. 컷 길이 중간값, 점무늬 간격과 각도, 물방울이 생기는 주기와 떨어지는 속도 같은 것들입니다.
3. 잰 숫자로 똑같이 만들며 학습합니다. 원본과 나란히 놓고, 두 영상을 겹친 차이 지도에서 제일 다른 곳부터 고칩니다. 판 번호를 올리며 반복하고, 받은 피드백은 기록합니다.
4. 내 브랜드로 바꿉니다. 틀만 남기고 글·색·로고를 교체합니다. 원본 음악과 화면은 연습에만 쓰고 올리지 않습니다.
5. 스킬로 저장합니다. 템플릿과 내용 파일(JSON)로 나눠 두면, 다음엔 불러와서 글만 바꾸면 됩니다.

## 설치 (Claude Code)

```bash
git clone https://github.com/yeronimo73/dawnstar-brand-video-skill.git
mkdir -p ~/.claude/skills && cp -r dawnstar-brand-video-skill/skills/* ~/.claude/skills/
```

필요한 프로그램: ffmpeg, python3, 그리고 `pip install numpy pillow`. Claude Code를 다시 시작하면 `brand-video-recreate` 스킬이 보입니다.

## 사용 예

따라 만들고 싶은 영상의 링크나 파일만 건네면 됩니다.

```
이 영상 따라 만들고 싶어. brand-video-recreate 스킬로 1~2단계부터 해 줘.
https://www.instagram.com/reel/게시물ID/
```

```
./ref/src.mp4 를 원본 프레임 전부 뽑아서 컷 길이 중간값이랑 장면표부터 만들어 줘.
측정은 표로 정리하고, 추정한 값은 추정이라고 따로 적어.
```

```
v2를 만들었어. 원본이랑 나란히 놓고 차이 지도 돌려서, 제일 다른 곳 세 군데부터 고쳐 줘.
브랜드 색은 #CF1830, 로고는 ./assets/logo.svg 로 바꿔서 4단계도 해 줘. 원본 음악은 빼고.
```

## 구성

```
skills/brand-video-recreate/
  SKILL.md              다섯 단계: 할 일, 산출물, 검수 기준, 자주 틀리는 점
  scripts/
    extract_frames.sh   전 프레임(또는 초당 n장) 뽑기
    contact_sheet.py    프레임을 격자로 펼친 접촉표
    cut_lengths.py      컷 감지, 컷 수, 길이 중간값·분포
    side_by_side.sh     원본 | 재현 나란히 영상
    diff_map.py         두 영상의 프레임 차이 히트맵과 평균 차이
    dot_pitch.py        점무늬 간격·각도 (푸리에 변환)
    region_series.py    한 영역의 값을 프레임별 표(CSV)로
  templates/            측정 기록, 판별 기록, 내용 JSON 예시
prompts/                영상 여섯 편의 실제 지시문, 피드백, 측정 숫자, 작업 순서
  oldfilm.md  liquid-text.md  motion-showreel.md
  template-cube.md  paper-collage.md  3d-keyboard.md
docs/minho-neck.md      캐릭터 말하기: 목·어깨 움직임 계산
```

스크립트는 단독으로도 씁니다.

```bash
skills/brand-video-recreate/scripts/extract_frames.sh ref/src.mp4 ref/frames all
python3 skills/brand-video-recreate/scripts/cut_lengths.py ref/src.mp4
python3 skills/brand-video-recreate/scripts/diff_map.py ref/src.mp4 out/v1.mp4 --heat-dir qa/heat
```

## 주의

- 참고 영상은 학습용입니다. 이 저장소에는 남의 영상·이미지·음악이 들어 있지 않고, 참고작은 제작자 계정과 게시물 ID로만 적었습니다.
- 연습으로 만든 영상(원본 음악, 원본 화면이 들어간 판)은 올리지 마세요. 올리는 영상은 4단계를 거쳐 글·색·로고·소리를 모두 내 것으로 바꾼 것이어야 합니다.
- `prompts/`의 숫자는 그 영상 하나에서 잰 값입니다. 다른 영상에 그대로 쓰는 값이 아니라, 무엇을 어떻게 재는지 보여 주는 예입니다.

## 라이선스

MIT. 던스타.
