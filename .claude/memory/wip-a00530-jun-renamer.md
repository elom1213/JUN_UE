---
name: wip-a00530-jun-renamer
description: "JUN_UE A00530 JUN Renamer - Asset Renamer 이식 + Trim/Copy Name, v01.01 부터 EUW 도킹 탭. 설계 판단과 에디터 미확인 사항"
metadata:
  type: project
---

`JUN_UE` 의 A00530_jun_renamer (툴 v01.01 / 플러그인 v01.05, 2026-11-20). 원본은 MANUProject
`Plugins/MANUEditor` 의 `SMANUAssetRenamerWidget`(C++ Slate) + `AssetRenameRules.csv`.

**사용자 최우선 요구: 창을 띄운 채 콘텐츠 브라우저를 클릭할 수 있어야 한다** → v01.01 에서 모달 다이얼로그를
EUW 도킹 탭으로 바꿨다. `Content/A00530_jun_renamer/EUW_JUNRenamer`(사용자가 **UE 5.4** 에디터에서 제작,
루트 = 변수 `DetailsView` 하나, Tab Display Name = `JUN Renamer`) 에 설정 오브젝트를 `set_object()`.
EUW 실패 시 모달로 대체. 계획서 `Docs/Plans/A00530_JUNRenamer_EUW_Tab_Plan.md`.

**설계 판단 (사용자가 바꾸자고 하면 여기부터)**
- `-1 Front` / `-1 Rear` 는 마야처럼 즉시 리네임이 **아니다** — `Trim Front/Rear` 횟수를 올리고 미리보기,
  `Rename` 한 번에 실행. 에셋 리네임은 저장·참조 수정이 따라와서.
- 마야 `Set suffix`(세트 전용) → 조건 없는 `Suffix`. 언리얼엔 세트가 없고 같은 폴더 충돌은 `Name taken` 이 잡는다.
- `Use Naming Convention` 기본 **꺼짐**(원본은 켜짐) — 원본 CSV 의 버릇(텍스처 줄 열 밀림으로 전부 `_DIF`,
  WBP → `BP_`)을 그대로 옮겼기 때문. 고치려면 CSV 수정.
- 저장은 바꾼 에셋만 (원본 `SaveDirtyPackages` 전체 저장을 좁힘).
- 열 때 선택 자동 불러오기는 목록이 비었을 때만. 클래스 · 오브젝트는 세션 모듈 `_jun_tools_session` 에.

**v01.02 스파이크 (원본 모양 UI)**: 사용자가 EUW 루트를 `VerticalBox` `Root` 로 바꿈 → `ui_tab.py` 가 실행 중에
위젯을 조립(위: 원본 모양 일부, 아래: 파이썬 생성 DetailsView). 화면에 그려지는지 확인되면 나머지를 옮기고
설정 패널을 걷어낸다 — **그 전에 계획서**(사용자는 큰 작업 전에 계획서를 원한다). UI 문자열은 영어만
(사용자 재강조 2026-11-20: 언급하지 않으면 UI 에 한국어 금지).

**v01.03**: 사용자 스크린샷으로 탭이 실제로 뜨고 파이썬 위젯이 그려지는 것은 확인됨(글자가 커서 에디터 스타일로 교체,
버린 버튼 콜백이 GC 로 죽던 것 수정). **v01.04**: `Mode:` 콤보로 Default / Copy Name. Copy Name = 공용 `AssetList`
두 개(Base / Targets, 각 리스트 아래 `Sort` — v01.07 에서 이름 통일) + 칸 + 미리보기 + Copy Name 버튼. 설정 패널은 `categories_to_show`
로 Assets · Rename 만. 사용자는 공용 위젯을 마야 Framework 처럼 키우길 원한다 → `jun_tools/widgets/` · `Docs/Widgets/`.

**미확인 (에디터 눈 확인 대기)**: v01.04 화면 배치(두 리스트 · 모드 전환), 리스트 행 클릭 시 콘텐츠 브라우저 이동.
헤드리스 71/71(5.4 · 5.7)은 로직만 증명.

관련: [[unreal-python-tool-verify]], [[wip-a00510-bone-viewport]], [[jun-ue-plugin-repo]]
