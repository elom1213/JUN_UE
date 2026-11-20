---
name: wip-a00530-jun-renamer
description: "JUN_UE A00530 JUN Renamer - MANUEditor Asset Renamer(C++) 파이썬 이식 + A00330 Trim/Copy Name. 설계 판단과 미확인 사항"
metadata:
  type: project
---

`JUN_UE` 의 A00530_jun_renamer (툴 v01.00 / 플러그인 v01.04, 2026-11-20). 원본은 MANUProject
`Plugins/MANUEditor` 의 `SMANUAssetRenamerWidget`(C++ Slate) + `AssetRenameRules.csv`.

**설계 판단 (사용자가 바꾸자고 하면 여기부터)**
- `-1 Front` / `-1 Rear` 는 마야처럼 즉시 리네임이 **아니다** — `Trim Front/Rear` 횟수를 올리고 미리보기,
  `Rename` 한 번에 실행. 에셋 리네임은 저장·참조 수정이 따라와서.
- 마야 `Set suffix`(세트 전용) → 조건 없는 `Suffix`. 언리얼엔 세트가 없고 같은 폴더 충돌은 `Name taken` 이 잡는다.
- `Use Naming Convention` 기본 **꺼짐**(원본은 켜짐) — 원본 CSV 의 버릇(텍스처 줄 열 밀림으로 전부 `_DIF`,
  WBP → `BP_`)을 그대로 옮겼기 때문. 고치려면 CSV 수정.
- 저장은 바꾼 에셋만 (원본 `SaveDirtyPackages` 전체 저장을 좁힘).

**미확인**: 실제 에디터에서 창 모양 · 버튼 배치 · 배열 미리보기 가독성. 헤드리스 31/31 은 로직만 증명.

관련: [[unreal-python-tool-verify]], [[wip-a00510-bone-viewport]], [[jun-ue-plugin-repo]]
