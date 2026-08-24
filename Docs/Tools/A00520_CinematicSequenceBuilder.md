# A00520 — Cinematic Sequence Builder

MSEQ(마스터) / CSEQ(컷) / SSEQ(역할별 서브) **시퀀서 3계층과 폴더 구조를 한 번에 만들고 서로 물려준다.**

- **버전**: v01.00 (2026-08-24)
- **메뉴**: `Tools > JUN > Cinematic`
  - `Cinematic Sequence Builder...` — 생성 다이얼로그
  - `Validate Cinematic Structure` — 기존 씬 검사 (아무것도 만들지 않음)
- **모듈**: `jun_tools/tools/A00520_cinematic_sequence_builder/`
- **설정**: `Config/jun_cinematic_sop.json`
- **계획서**: [../Plans/A00520_CinematicSequenceBuilder_Plan.md](../Plans/A00520_CinematicSequenceBuilder_Plan.md)
- **프로토타입**: [../Plans/seq_batch_tool_ue57.py](../Plans/seq_batch_tool_ue57.py)

---

## 왜 만들었나

씬 하나를 손으로 만들면 이렇게 된다 (`Teaser/CT01` 기준, 5씬 66컷):

```
MSEQ            =   5개
씬 SSEQ   5 × 7 =  35개
CSEQ            =  66개
컷 SSEQ  66 × 7 = 462개
────────────────────────
합계              568개  + 폴더 200여 개 + 결선 533회 + 컬러 지정 533회
```

한 편당 하루가 넘는 반복 작업이고, 실제로 사고가 났다 —
`Teaser/CT01/S02` 폴더 안의 마스터 이름이 `MSEQ_MANU_PreDebut_CT01_S01` 이다.
`TSR` 이 빠졌고 **씬 번호가 S01 로 잘못 들어갔으며**, 같은 폴더의 SSEQ 7개도 전부 `_S01_` 이다.
같은 CT 안에서도 `MANU_` 토큰이 있는 씬과 없는 씬이 갈린다.

자동화의 목적은 시간 절약보다 **한 씬 안에서 이름이 갈리지 않게 하는 것**에 있다.

---

## 만들어지는 구조

```
<Root Path>/<S##>/
├── MSEQ_<stem>_<S##>                     ← 렌더 진입점
│     ├─ Cinematic Shot Track  : CSEQ N개를 시간축에 순차 배치
│     └─ Sub Track ×7          : 씬 레벨 SSEQ
├── Map/                                   (옵션)
├── Animation/                             (옵션)
├── Subsequence/
│   └── SSEQ_<stem>_<S##>_{ANIM,CAM,LGT,VFX,Sound,LayoutAdjust,Media}
└── C0010/ C0020/ ...
    ├── CSEQ_<stem>_<S##>_<C####>
    │     ├─ Sub Track ×7      : 컷 SSEQ
    │     └─ Camera Cut Track  : 비어 있음 (컷 작업 시 채운다)
    ├── Animation/  VFX/                   (옵션)
    └── Subsequence/
        └── SSEQ_<stem>_<S##>_<C####>_{7종}
```

SSEQ 7종은 전부 **빈 시퀀스**다. 단, `CAM` 만 예외로 카메라 초기 셋업이 들어간다 (아래).

근거: `docs/DnableSOP/007 Cinematic/001 Key Base.md` + 실제 `Teaser/CT01/S01` 에셋 바이너리 실측.

---

## Name Stem — 이름은 사용자가 정한다

**`MANU_` 를 코드에도 설정 기본값에도 넣지 않았다.** 접두 부분은 UI 텍스트 필드에 직접 친다.

| Name Stem 입력 | 만들어지는 마스터 |
|---|---|
| `PreDebut_TSR_CT01` | `MSEQ_PreDebut_TSR_CT01_S06` |
| `MANU_PreDebut_TSR_CT01` | `MSEQ_MANU_PreDebut_TSR_CT01_S06` |

툴은 이 문자열을 **해석하지 않는다.** 템플릿 `MSEQ_{stem}_{scene}` 에 그대로 끼워 넣을 뿐이다.
"정답 이름"을 툴이 강요하지 않으면서, 한 번 정한 stem 이 그 씬 전체 100여 개 에셋에
동일하게 적용된다. 위 `S02` 같은 사고가 구조적으로 불가능해진다.

마지막 입력값은 `Saved/JUNTools/a00520_last.json` 에 남아 다음 실행 때 채워진다 —
같은 CT 의 다음 씬을 만들 때 다시 타이핑하지 않게 하려는 것이고, **씬 간 일관성**도 따라온다.

> 콘텐츠 타입 약어(`Teaser`→`TSR` 등)의 정본은 아직 확인 중이다.
> 그래서 `content_types` 는 비워 두었다. Stem 자유 입력이 그 자리를 대신하므로 막히는 것은 없다.

---

## 사용법

### 1. 대상 폴더를 콘텐츠 브라우저에서 고른다

`.../Teaser/CT01` 처럼 **씬이 들어갈 챕터 폴더**를 고른다. 다이얼로그의 `Root Path` 가 자동으로 채워진다.

### 2. `Tools > JUN > Cinematic > Cinematic Sequence Builder...`

| 항목 | 설명 |
|------|------|
| **Root Path** | 씬이 들어갈 폴더. 콘텐츠 브라우저 선택에서 자동 획득, 직접 고쳐도 된다 |
| **Name Stem** | ★ 위 참조. 자유 텍스트 |
| **Scene Number** | `6` → `S06` |
| **Cut Start / Count / Step** | `10 / 13 / 10` → `C0010` ~ `C0130` |
| **Frames Per Cut** | 컷 하나의 임시 길이. 마스터에서 컷이 이 길이만큼 이어 붙는다 |
| **Display Rate (fps)** | 기본 30 |
| Create Scene Subsequences | 씬 레벨 SSEQ 7종 |
| Create Cut Subsequences | 컷마다 SSEQ 7종 |
| **Set Up CineCamera in CAM** | CAM SSEQ 에 카메라 초기 셋업 |
| Apply SOP Folder Colors | 시퀀서 폴더 그룹 + SOP 컬러 |
| Create Map / Animation Folders | 부수 폴더 |
| **Dry Run First** | 기본 켜짐. 아래 참조 |

### 3. Dry Run → 확인 → 생성

모달 디테일 뷰는 실시간 미리보기가 안 된다. 그래서 2단계로 나눴다.

```
① OK       → 값 확정
② Dry Run  → Output Log 에 만들어질 에셋 이름 전체 출력
③ 확인창   → "Create 112 assets?"  ← 이름을 눈으로 보고 결정
④ OK       → 실제 생성
```

`Dry Run First` 를 끄면 ②③ 을 건너뛴다.

---

## CAM 서브시퀀스 카메라 셋업

`Set Up CineCamera in CAM` 을 켜면 CAM SSEQ 안에 이것들이 생긴다:

- 스포너블 `CineCameraActor` (이름 = `{stem}_{scene}_{cut}_camera`)
- `CineCameraComponent` Possessable 바인딩 (액터 바인딩의 자식)
- `Camera Cut Track` + 섹션 (카메라 바인딩 ID 연결됨)
- 액터 / 컴포넌트 `3D Transform Track`
- `Float Track` ×3 — `CurrentFocalLength`, `CurrentAperture`, `FocusSettings.ManualFocusDistance`

**왜 이 조합인가**: 실측한 `SSEQ_PreDebut_TSR_CT01_S01_C0010_CAM.uasset` 에서 추출한 클래스 목록과
프로토타입 출력이 **프로퍼티 경로까지 일치**했다. 아티스트가 손으로 하던 초기 셋업 그대로다.

> 이미 카메라 컷 트랙이 있는 CAM SSEQ 는 건드리지 않는다.
> 셋업 중 임시 `CineCameraActor` 를 레벨에 잠깐 스폰했다가 지운다 — 실패해도 `finally` 로 지운다.

---

## Validate — 만들지 않고 검사만

콘텐츠 브라우저에서 `S##` 폴더를 고르고 `Tools > JUN > Cinematic > Validate Cinematic Structure`.

| 검사 | 심각도 |
|------|--------|
| **씬 안에서 Name Stem 이 갈림** | ERROR |
| 에셋 이름의 씬/컷 번호가 폴더와 불일치 | ERROR |
| 디스크에 있는데 마스터/CSEQ 에 결선 안 됨 | ERROR |
| SSEQ 7종 중 누락 | WARNING |
| 7종에 없는 접미사 | WARNING |
| 마스터가 2개 이상 | WARNING |
| 씬 루트의 정체불명 에셋 (`UE_Placeholder` 등) | INFO |

결과는 Output Log 와 `Saved/JUNTools/cinematic_validate_<S##>.csv`.

**stem 의 "정답"을 강요하지 않는다.** 씬 안에서 하나로 통일돼 있는지만 본다.

---

## 안전장치

| 항목 | 동작 |
|------|------|
| **비파괴 / 멱등** | 생성 전 `does_asset_exist()` 전수 확인. 이미 있으면 만들지 않고 **결선만 보수**한다. 두 번 돌려도 중복이 생기지 않는다 |
| **이름 충돌** | 같은 이름의 다른 타입 에셋이 있으면 **아무것도 만들지 않고** 중단하고 목록을 찍는다 |
| **Undo** | `ScopedEditorTransaction` 으로 묶는다 (에셋 생성의 롤백은 엔진 보장 밖 — 아래 한계 참조) |
| **취소** | `ScopedSlowTask` 진행률 + 취소. 취소하면 그때까지 만든 것은 남고 경고를 남긴다 |
| **저장 범위** | 우리가 **만들었거나 결선한 에셋만** 저장한다. 경로 아래를 통째로 저장하지 않는다 |
| **기존 마스터** | 이미 있는 마스터의 재생 범위·프레임레이트는 건드리지 않고 경고만 남긴다 |
| **SVN** | 툴은 버전관리를 **절대 호출하지 않는다.** 생성 후 `N assets created - remember to add them to SVN` 을 로그에 남긴다 |

---

## 설정 (`Config/jun_cinematic_sop.json`)

이름 템플릿 · SSEQ 7종 · 컬러코드 · 카메라 float 트랙 · 프레임레이트가 전부 여기 있다.
**코드에는 이름 규칙이 한 글자도 없다.**

`<Project>/Config/jun_cinematic_sop.json` 을 두면 최상위 키 단위로 덮어쓴다.
`008 Prefix Suffix Rules.md` 가 시네마틱 Prefix 를 *"추후 확정 예정"* 으로 못박고 있으므로,
규격이 바뀌면 **JSON 만 고치면 된다.**

---

## 콘솔 / 커맨드렛에서 쓰기

`core` 는 UI 에 의존하지 않는다.

```python
from jun_tools.tools.A00520_cinematic_sequence_builder import core

# 계획만 본다
core.build_uniform(
    root_path="/Game/MANUCinematic/PreDebut/Teaser/CT01",
    stem="PreDebut_TSR_CT01",
    scene_number=6,
    cut_start=10, cut_count=13, cut_step=10, frames_per_cut=120,
    dry_run=True,
)

# 실제로 만든다
core.build_uniform(..., dry_run=False)

# 검사
core.validate("/Game/MANUCinematic/PreDebut/Teaser/CT01/S02")
```

---

## 엔진 버전 대응

`compat.py` 하나에 버전차 흡수 로직을 모았다. 프로토타입이 5.7 에서 실제로 겪은 사고가 근거다 —
`LevelSequence.add_master_track` 이 버전에 따라 있기도, 없기도 하다.

```python
add_track  →  MovieSceneSequenceExtensions.add_track
           →  add_master_track  →  Extensions.add_master_track
```

후보를 순서대로 시도하고 첫 성공을 쓴다. 엔진이 5.8 로 올라가 API 가 또 갈리면 **이 파일만 고친다.**

없어도 되는 기능(폴더 컬러 · 트랙 틴트 · 샷 표시 이름)은 실패를 삼키고 `True/False` 를 돌려준다.
호출부가 경고를 한 번 남기고 계속 진행한다 — 컬러가 안 된다고 568개 생성이 멈추면 안 되기 때문이다.

---

## 검증

`Docs/verify/verify_sequencer_api.py` 를 **스크래치 프로젝트에** 헤드리스로 돌린다.
사내 프로젝트에 돌리지 말 것 — 에셋을 만들었다 지운다.

```bash
UnrealEditor-Cmd.exe <Scratch>.uproject -run=pythonscript \
    -script="Docs/verify/verify_sequencer_api.py" -unattended -nosplash -nullrhi \
    -AbsLog="verify_sequencer.log"
```

로그에서 `[A00520-VERIFY]` 를 grep 한다. 항목: 트랙 추가 바인딩, 서브섹션 결선, CinematicShotTrack,
폴더/컬러, 시퀀스 설정, 카메라 셋업, 트랜잭션, 그리고 `core.build_uniform` 왕복 + **멱등성** + Validate.

> **아직 실측되지 않았다.** 아래 세 가지는 계획서 §7 에서 "미확인"으로 남겨둔 항목이고,
> 이 검증 스크립트를 돌리기 전까지는 답이 확정되지 않는다.
> 결과가 나오면 이 문단을 실측 표로 교체할 것.

| 항목 | 상태 | 안 될 경우 |
|------|------|-----------|
| `MovieSceneCinematicShotTrack` | 미확인 | SubTrack 으로 폴백 + **경고**. 마스터 구조가 실측과 달라지므로 렌더 전 확인 필요 |
| 폴더 생성 / 폴더 컬러 | 미확인 | 컬러 없이 진행 + 경고 |
| 트랙 틴트 | 미확인 | 동일 |

---

## 한계

- **에셋 생성은 Ctrl+Z 로 되돌아가지 않을 수 있다.** `ScopedEditorTransaction` 으로 묶었지만
  에셋 생성의 롤백은 엔진이 보장하지 않는다. 그래서 툴은 만든 것을 전부 로그에 남긴다.
- **모달 디테일 뷰라 실시간 미리보기가 없다** (설계 가이드 §10). Dry Run 이 그 자리를 대신한다.
- **컷별 길이를 따로 줄 수 없다.** 지금은 균등 길이만. `spec.make_cuts_from_list()` 가 이미
  있으므로 JSON 컷리스트 입력은 UI 만 붙이면 된다 (계획서 Phase 5).
- **ML/SL 레벨(`.umap`)은 만들지 않는다.** 폴더만 만든다. 배경 에셋에 의존하는 작업이다.
- **기존의 잘못된 이름을 고치지 않는다.** 참조가 걸린 에셋의 리네임은 별개 작업이다.
  Validate 가 보고만 한다.
- **카메라 셋업은 열린 레벨이 있어야 한다.** 임시 액터를 스폰하기 때문이다.
