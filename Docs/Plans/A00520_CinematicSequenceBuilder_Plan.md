# A00520 — Cinematic Sequence Builder · 제작 계획서

> MSEQ(마스터) / CSEQ(컷) / SSEQ(역할별 서브) 시퀀서 3계층과 디렉토리 구조를
> SOP 규격대로 **한 번에 생성하고 서로 물려주는** 언리얼 에디터 툴.

- **작성일**: 2026-08-24
- **개정**: 2026-08-24 (rev.2) — 프로토타입 `seq_batch_tool_ue57.py` 반영, 네이밍 UI 방식 변경
- **작성자**: Ji Hun Park (Junny)
- **대상 저장소**: `JUN_UE` (플러그인 `JUNTools`)
- **툴 번호**: `A00520_cinematic_sequence_builder` (A00500 hello, A00510 bone_viewport 다음)
- **상태**: **구현 완료 (2026-08-24)** — Phase 1~4 코드 작성됨. **Phase 0 헤드리스 실측 미완**
  → 툴 문서: [../Tools/A00520_CinematicSequenceBuilder.md](../Tools/A00520_CinematicSequenceBuilder.md)
  → 검증 스크립트: [../verify/verify_sequencer_api.py](../verify/verify_sequencer_api.py)
- **선행 문서**: [00_UE_Tool_Plugin_Guide.md](../00_UE_Tool_Plugin_Guide.md)
- **프로토타입**: [`seq_batch_tool_ue57.py`](seq_batch_tool_ue57.py) (같은 폴더, 386줄)

---

## 0. 요약

| 항목             | 결론                                                                   |
| -------------- | -------------------------------------------------------------------- |
| 기존 툴이 있는가      | 프로젝트에 배포된 툴은 **없다**. 다만 **동작하는 프로토타입이 있다** (§1.4)                    |
| 규격 문서는 있는가     | **있다.** `docs/DnableSOP/007 Cinematic/001 Key Base.md` 가 사실상 스펙 (§2) |
| 어디에 만드는가       | `JUN_UE` 플러그인의 새 툴 `A00520` — Python 콘텐츠 플러그인, 컴파일 불필요               |
| 무엇을 만드는가       | 폴더 + MSEQ/CSEQ/SSEQ 생성 + SubTrack/ShotTrack 결선 + CAM 카메라 셋업 + 폴더 컬러  |
| 프로토타입을 어떻게 쓰는가 | **API 검증 자산으로 전량 흡수.** 계층·네이밍·안전장치는 새로 짠다 (§5.7)                     |
| 네이밍 정책         | **`MANU_` 를 코드에 넣지 않는다.** 사용자가 UI 에서 직접 입력한 텍스트를 쓴다 (§5.2, §5.6)     |
| 핵심 원칙          | **비파괴**(기존 에셋 덮어쓰지 않음) · **설정 외부화** · **Dry-run 우선**                 |

---

## 1. 사전 조사 결과

### 1.1 조사 범위와 방법

| 대상 | 방법 | 결과 |
|------|------|------|
| `C:\MANUSetup\docs` (A) | 전체 트리 + `MSEQ / SSEQ / CSEQ / 시퀀스 생성` grep | 규격 문서만 존재, 툴 언급 없음 |
| `C:\MANUSetup\MANUProject\Docs` (B) | 전체 트리 + 동일 grep | 시퀀서를 *쓰는* 문서만 존재, 생성 툴 없음 |
| `MANUProject/Plugins/MANUEditor` | 소스 65개 파일 목록 + 기능 문서 8개 | 리네이머 · 레벨정리 · 청크분석 · LookDev … **시퀀서 생성 기능 없음** |
| `MANUProject/Plugins/JUN` | 전체 | `A00500_hello`, `A00510_bone_viewport` 둘뿐 |
| 워크스페이스 전체 코드 | `LevelSequenceFactoryNew / MovieSceneSubSection / MovieSceneCinematicShotTrack / create_level_sequence` grep | **히트 0건** |
| Content 내 EUW/EUB | `*EUW*`, `*EUB*`, `*Builder*`, `*Generator*`, `*Setup*` 검색 | 시퀀서 관련 유틸리티 위젯 없음 |
| 루트 `Tools/`, `src/manu/` | 디렉토리 스캔 | Notion · FaceShadowSDF · StreamDeck · 대시보드 등. 시네마틱 무관 |

### 1.2 프로젝트에 배포된 툴은 없다

현재 `Teaser/CT01/S01~S05` 의 구조는 **수작업**으로 만들어진 것으로 판단된다. 근거:

- `S01` 은 `MSEQ_PreDebut_TSR_CT01_S01`, `S03~S05` 는 `MSEQ_MANU_PreDebut_TSR_CT01_S0N`
  → **`MANU_` 토큰 유무가 갈린다**
- `S02` 폴더 안의 마스터 이름이 `MSEQ_MANU_PreDebut_CT01_S01` — **`TSR` 누락 + 씬 번호가 S01로 오기**
  (같은 폴더의 SSEQ 7개도 전부 `..._S01_...` 로 잘못 들어가 있다)
- `S05` 에 `UE_Placeholder.uasset` 이 남아 있음

### 1.3 문서 경로 (툴은 없지만 **규격은 여기 있다**)

| 경로 | 내용 |
|------|------|
| `C:\MANUSetup\docs\DnableSOP\007 Cinematic\001 Key Base.md` | **★ 정본 스펙.** S##/C#### 구조, MSEQ/CSEQ/SSEQ 명명, SSEQ 7종, 컬러코드, 렌더 드라이브 |
| `C:\MANUSetup\docs\DnableSOP\006 SetDressing\002 Cinematic.md` | 서브레벨(ML/SL) 구조, LayoutAdjust 연동 |
| `C:\MANUSetup\docs\DnableSOP\002 Common\008 Prefix Suffix Rules.md` §1.4 | 시네마틱 Prefix 표 — *"추후 확정 예정, 잠정 규칙"* 명시 |
| `C:\MANUSetup\docs\DnableSOP\002 Common\002 Naming Rules.md` | 공통 네이밍 |
| `C:\MANUSetup\MANUProject\Docs\Development\Plugins\MANUEditor.md` | 사내 에디터 플러그인 기능 목록 (여기 없다는 근거) |

### 1.4 프로토타입 `seq_batch_tool_ue57.py` — **가장 값진 입력**

386줄. 콘솔에서 `generate_sequences_for_shots("SCH", 10)` 로 호출하는 배치 생성 스크립트다.
이 파일의 진짜 가치는 기능이 아니라 **UE 5.7 Python 바인딩을 실제로 통과한 호출 조합**에 있다.
계획서 rev.1 의 Phase 0(API 검증)이 요구하던 항목 대부분이 여기서 이미 답이 나와 있다.

#### 프로토타입이 만드는 구조 (우리 SOP와 다름)

```
root/SEQCODE/
├── SEQ_master_SEQCODE              ← 만들기만 하고 샷을 안 넣는다 (374줄 주석 처리)
└── SEQCODE_01010/
    ├── SEQ_SEQCODE_01010           ← 샷 메인
    └── Sub/
        ├── SEQ_anim_SEQCODE_01010
        ├── SEQ_cam_SEQCODE_01010   ← CineCamera + CameraCut 자동 셋업 ★
        └── SEQ_lgt_SEQCODE_01010
```

2계층(master → shot → sub 3종). 우리는 3계층(MSEQ → CSEQ → SSEQ 7종) + 씬 레벨 SSEQ 7종.

#### 그대로 가져올 자산

| # | 프로토타입 | 왜 값진가 |
|---|-----------|----------|
| P1 | `_call_first_working(calls, context)` + `*_compat()` 4종 (70~141줄) | **UE 버전 간 바인딩 차이를 후보 목록으로 흡수하는 패턴.** `add_master_track` → `MovieSceneSequenceExtensions.add_master_track` → `add_track` 순으로 시도. 5.7에서 `add_master_track` 이 사라진 실제 사고를 이미 처리해 놓았다 |
| P2 | `get_root_path_from_content_browser()` (41~61줄) | `EditorUtilityLibrary.get_selected_folder_paths()` → `get_current_content_browser_path()` → fallback. **rev.1 에서 "디렉토리 피커"라고 뭉뚱그린 것보다 훨씬 낫다.** 사용자가 콘텐츠 브라우저에서 폴더만 고르면 끝 |
| P3 | `create_level_sequence()` (23~33줄) | `AssetToolsHelpers.get_asset_tools().create_asset(..., unreal.LevelSequence, unreal.LevelSequenceFactoryNew())` — 검증됨 |
| P4 | `ensure_directory()` (16~20줄) | `EditorAssetLibrary.does_directory_exist` / `make_directory` — 검증됨 |
| P5 | 서브 결선 3줄 (161~170줄) | `track.add_section()` → `section.set_sequence(seq)` → `section.set_range(a, b)` — 검증됨 |
| P6 | **`setup_cam_sequence_with_cine()` (176~276줄)** | **이게 최대 수확.** 아래 별도 설명 |

#### P6 — CAM 서브시퀀스 카메라 셋업이 실제 에셋과 일치한다

프로토타입이 `cam_seq` 안에 만드는 것:

- 임시 `CineCameraActor` 스폰 → `add_spawnable_from_instance()` 로 **스포너블 바인딩** → 임시 액터 삭제
- `CineCameraComponent` 를 **Possessable 로 추가하고 액터 바인딩의 자식으로 설정**
- `MovieSceneCameraCutTrack` + 섹션 + `get_binding_id()` 로 **카메라 바인딩 연결**
- 액터 `MovieScene3DTransformTrack`, 컴포넌트 `MovieScene3DTransformTrack`
- `MovieSceneFloatTrack` ×3 — `CurrentFocalLength` / `CurrentAperture` / `FocusSettings.ManualFocusDistance`
  (`MovieScenePropertyTrackExtensions.set_property_name_and_path()`)
- 스포너블 이름을 `<베이스>_camera` 로 리네임 (`MovieSceneBindingExtensions.set_name()`)
- 빈 바인딩 정리 (`remove_binding` 이 없을 수 있어 폴백 + 경고)

이걸 실측한 `SSEQ_PreDebut_TSR_CT01_S01_C0010_CAM.uasset` (32KB) 의 내용과 대조하면:

| 실제 에셋에서 추출된 클래스 | 프로토타입이 만드는가 |
|---|---|
| `MovieSceneSpawnableActorBinding`, `CineCameraActor` | ✅ |
| `MovieSceneCameraCutTrack` / `MovieSceneCameraCutSection` | ✅ |
| `MovieScene3DTransformTrack` / `Section` | ✅ |
| `MovieSceneFloatTrack` ×3 — `CineCameraComponent:CurrentAperture`, `CurrentFocalLength`, `FocusSettings:ManualFocusDistance` | ✅ **프로퍼티 경로까지 동일** |
| `MovieScenePossessable`, `MovieSceneObjectBindingID` | ✅ |

**우연이 아니다.** 아티스트가 손으로 만들던 CAM 초기 셋업과 프로토타입 출력이 같다.
→ rev.1 에서 "비목표(아티스트 영역)"로 뺐던 **CAM 자동 셋업을 목표로 승격한다** (§3.1-6).

#### 그대로 쓰면 안 되는 것

| # | 문제 | 조치 |
|---|------|------|
| D1 | **비파괴 아님** — `does_asset_exist()` 확인이 없다. 재실행하면 `SEQ_..._1`, `_2` 가 쌓이거나 실패 | 전수 사전 확인 + SKIP (§5.4) |
| D2 | **Undo 없음** — `ScopedEditorTransaction` 미사용. 중간 실패 시 반쯤 만들어진 채로 남는다 | 트랜잭션으로 감쌈 |
| D3 | **Dry-run 없음** — 실행 전에 무엇이 생길지 알 수 없다 | 계획 수립 → 리포트 → 확인 → 실행 2단계 (§5.4) |
| D4 | **진행률/취소 없음** — 568개 생성 시 에디터가 응답 없이 멈춘다 | `ScopedSlowTask` (§7 위험표) |
| D5 | `save_all_under()` 가 `save_directory(recursive=True)` — **경로 아래 남의 더티 에셋까지 저장** | 생성한 에셋 목록만 `save_asset()` |
| D6 | `set_range(0, duration)` 고정 — 모든 섹션이 0부터 시작 | 마스터의 샷은 **누적 오프셋**으로 순차 배치 (§5.4) |
| D7 | **마스터에 샷을 안 넣는다** (374줄이 주석) — `MovieSceneCinematicShotTrack` 미사용 | MSEQ 는 ShotTrack 으로 CSEQ 배치 (§2.2 실측) |
| D8 | 네이밍 하드코딩 — `SEQ_master_`, `f"{n:05d}"`, `seq_name.replace("SEQ_cam_", "")` | 템플릿화 (§5.2). 특히 `replace()` 로 이름을 역파싱하는 방식은 규칙이 바뀌면 조용히 깨진다 |
| D9 | `EditorLevelLibrary` 사용 (187줄) — UE5 에서 deprecated 경고 대상 | `EditorActorSubsystem` 우선 + 폴백 (§7 A8) |
| D10 | 폴더/컬러 없음, 7종 아닌 3종, 씬 레벨 SSEQ 없음 | 본 계획대로 확장 |
| D11 | UI 없음 (콘솔 호출) | `EditorDialog` 다이얼로그 (§5.6) |

---

## 2. 만들 구조 — 실측으로 확인한 사양

`Teaser/CT01/S01` 을 `.uasset` 바이너리에서 직접 읽어 확인했다. SOP 문서와 실제 에셋이 일치한다.

### 2.1 디렉토리

```
Content/MANUCinematic/<Project>/<ContentType>/<CT##>/<S##>/
├── MSEQ_<Stem>_<S##>.uasset              마스터 (렌더 진입점)
├── Map/
│   ├── ML_<Stem>_<S##>.umap              메인레벨
│   ├── SL_<Stem>_<S##>_LGT.umap          라이팅 서브레벨
│   └── SL_<Stem>_<S##>_LGT_<CHAR>.umap   캐릭터별 라이팅 (선택)
├── Subsequence/                          씬 전체 서브시퀀스 7종
│   └── SSEQ_<Stem>_<S##>_{ANIM,CAM,LGT,VFX,Sound,LayoutAdjust,Media}.uasset
├── Animation/                            씬 공용 애니메이션
└── C0010/ C0020/ ... /                   컷
    ├── CSEQ_<Stem>_<S##>_<C####>.uasset  컷 시퀀스
    ├── Animation/v001/                   AS_<Stem>_<S##>_<C####>_MANU_CH_<CHAR>_v001
    ├── VFX/                              컷 전용 단발성 VFX
    └── Subsequence/                      컷 서브시퀀스 7종
        └── SSEQ_<Stem>_<S##>_<C####>_{ANIM,CAM,LGT,VFX,Sound,LayoutAdjust,Media}.uasset
```

`<Stem>` = 사용자가 UI 에서 입력하는 자유 텍스트 (§5.2). 예: `PreDebut_TSR_CT01`

### 2.2 시퀀서 결선 — 실측

**MSEQ_PreDebut_TSR_CT01_S01.uasset (44KB)**:

| 트랙 | 클래스 | 담는 것 |
|------|--------|---------|
| Cinematic Shot Track | `MovieSceneCinematicShotTrack` / `MovieSceneCinematicShotSection` | **CSEQ 13개** (C0010~C0130), 시간축에 순차 배치 |
| Sub Track | `MovieSceneSubTrack` / `MovieSceneSubSection` | **씬 SSEQ 7개** |
| 정리 | `MovieSceneFolder` | 트리 폴더 그룹핑 |

**CSEQ_PreDebut_TSR_CT01_S01_C0010.uasset (24KB)**:

| 트랙 | 클래스 | 담는 것 |
|------|--------|---------|
| Sub Track | `MovieSceneSubTrack` / `MovieSceneSubSection` | **컷 SSEQ 7개** |
| Camera Cut Track | `MovieSceneCameraCutTrack` | 카메라 컷 |
| 정리 | `MovieSceneFolder` + **`FolderColor`** | 폴더 컬러코드가 실제로 적용되어 있음 |

**SSEQ_..._S01_LGT.uasset (3.2KB)** — 트랙 없음. **빈 LevelSequence**.
**SSEQ_..._C0010_CAM.uasset (32KB)** — CineCamera 스포너블 + CameraCut + Transform/Float 트랙.
→ **CAM 만 내용이 있고 나머지 6종은 빈 껍데기다.** 프로토타입 P6 가 정확히 이 CAM 을 만든다.

### 2.3 SSEQ 7종과 컬러코드 (SOP §9 정본)

| Type | 역할 | Folder Color | Track Color | 생성 시 내용 |
|------|------|-------------|-------------|---------------|
| `ANIM` | 애니메이션 | `#FF604F` | `#77474B` | 빈 시퀀스 |
| `CAM` | 카메라 | `#4DA1FB` | `#606E94` | **CineCamera 셋업** (§1.4 P6) |
| `LGT` | 라이팅 | `#FFED49` | `#9C946E` | 빈 시퀀스 |
| `VFX` | VFX | `#FF9E3B` | `#997E6D` | 빈 시퀀스 |
| `Sound` | 사운드 | `#A14FFF` | `#745380` | 빈 시퀀스 |
| `Media` | 미디어 | `#009416` | `#6E7F5C` | 빈 시퀀스 |
| `LayoutAdjust` | 레이아웃 조정 | `#00BFBA` | `#498583` | 빈 시퀀스 |

> 대소문자 주의: `ANIM/CAM/LGT/VFX` 는 전부 대문자, `Sound/Media/LayoutAdjust` 는 파스칼 케이스다.
> 실제 에셋도 이 규칙을 그대로 따른다. **문자열 상수로 박지 말고 설정 테이블로 관리한다.**

### 2.4 규모 — 왜 자동화가 필요한가

`Teaser/CT01` 한 편(S01~S05, 컷 66개) 기준:

```
MSEQ            =   5개
씬 SSEQ   5 × 7 =  35개
CSEQ            =  66개
컷 SSEQ  66 × 7 = 462개
────────────────────────
합계              568개  (+ 폴더 200여 개, 결선 533회, 컬러 지정 533회, CAM 셋업 71회)
```

같은 구조가 `ShortForm/CT01·CT02`, `CoverDance`, `StillCut`, `Demo`, `20260620_TechLive` 에도 반복된다.

---

## 3. 목표 / 비목표

### 3.1 목표

1. 씬 하나(`CT##/S##`)의 **폴더 + MSEQ + 씬 SSEQ 7개 + CSEQ N개 + 컷 SSEQ 7N개**를 한 번에 생성한다.
2. MSEQ ← CSEQ (**ShotTrack**), MSEQ ← 씬 SSEQ (SubTrack), CSEQ ← 컷 SSEQ (SubTrack) 을 **결선**한다.
3. SOP 컬러코드를 폴더/트랙에 적용한다.
4. **기존 에셋을 절대 건드리지 않는다.** 이미 있으면 건너뛰고 리포트한다. 두 번 돌려도 안전하다.
5. **Validate 모드**: 만들지 않고, 기존 씬이 SOP 규격에서 얼마나 벗어났는지만 리포트한다.
   (→ §1.2 의 `S02` 네이밍 사고를 잡아내는 것이 1차 실용 목표)
6. **CAM 서브시퀀스에 CineCamera 초기 셋업을 자동 생성한다** (rev.2 승격 — §1.4 P6). **옵션으로 끌 수 있다.**
7. **네이밍 접두 토큰을 사용자가 UI 에서 직접 입력한다.** 코드에 프로젝트명·`MANU_`·약어를 넣지 않는다.

### 3.2 비목표 (이번 범위 밖)

| 항목 | 이유 |
|------|------|
| CAM 외 SSEQ 내부 내용 (라이트 배치, 애니메이션 바인딩, VFX) | 아티스트 작업 영역 |
| ML/SL 레벨(`.umap`) 생성 | 배경 에셋 의존. 폴더만 만들고 레벨은 Phase 4 |
| 기존 잘못된 이름의 **자동 리네임** | 참조가 걸린 에셋을 건드리는 위험한 작업. Validate 리포트까지만 |
| MRQ / RG (렌더 큐) 생성 | 별도 툴 주제 |
| SVN add / commit | 툴이 버전관리를 건드리지 않는다 (§8) |
| 컷 길이 자동 산출 (EDL/편집본 파싱) | Phase 4 이후 |
| 콘텐츠 타입 약어 매핑 (`Teaser`→`TSR` 등) | **정본 확인 중 — 보류** (§9 Q2). Stem 자유 입력으로 우회 |

---

## 4. 배치 위치와 이유

**`JUN_UE` (JUNTools) 플러그인의 새 툴로 만든다.** `MANUEditor`(C++) 가 아니다.

| 후보 | 판단 |
|------|------|
| **JUNTools Python 툴** ✅ | 컴파일 불필요 · 에디터 재시작 없이 반복 개발 · 이식 가능 · **프로토타입이 이미 Python 으로 동작을 증명** |
| MANUEditor C++ 모듈 | 엔진 빌드에 묶임(가이드 §3①). 반복 수정이 잦은 파이프라인 툴에는 사이클이 너무 무겁다 |
| Editor Utility Widget (BP) | 바이너리 에셋이라 diff·머지 불가 |

프로토타입이 5.7 에서 도는 것을 확인해 준 덕분에, rev.1 에서 걱정하던 "Python API 로 도달 가능한가"는 사실상 해소됐다.
남은 미확인 영역은 **폴더 컬러 / 트랙 틴트 / CinematicShotTrack** 셋뿐이다 (§7).

---

## 5. 설계

### 5.1 모듈 구조

가이드 §9 "새 툴 추가 체크리스트"를 따른다. `core` 는 UI 무의존 → 커맨드렛에서 재사용 가능.

```
Content/Python/jun_tools/tools/A00520_cinematic_sequence_builder/
├── __init__.py
├── compat.py     ← 프로토타입 P1 이식. _call_first_working + add_track/possessable/parent/remove 폴백
├── naming.py     이름·경로 조립. 순수 문자열 로직 (unreal 임포트 없음 → 단위 테스트 가능)
├── spec.py       설정(JSON) 로드 + SceneSpec/CutSpec + 입력 검증
├── plan.py       생성 계획 수립 (CREATE / SKIP / CONFLICT). 실제 쓰기 없음 → Dry-run 의 근거
├── build.py      계획을 실행. 에셋 생성 · 결선 · 컬러
├── camera.py     ← 프로토타입 P6 이식. CAM SSEQ 의 CineCamera 셋업
├── validate.py   기존 씬 검사 리포트
├── core.py       진입점 3개: build(spec, dry_run) / validate(path) / preview(spec)
└── ui.py         show() — 다이얼로그. core 를 부르는 얇은 껍데기

Config/jun_cinematic_sop.json    ← SOP 규격 데이터 (플러그인 루트)
```

`compat.py` 를 **최하단 공용 모듈로 분리**하는 것이 프로토타입에서 배운 핵심이다.
버전차 흡수 로직이 여기 한 군데에만 있어야, 엔진이 5.8 로 올라갈 때 고칠 곳이 하나로 남는다.

### 5.2 네이밍 정책 — **하드코딩 금지, 사용자 입력 우선**

#### 결정 (rev.2)

- **`MANU_` 를 코드에도 설정 기본값에도 넣지 않는다.**
- 이름의 접두 부분(`{stem}`)은 **UI 텍스트 필드에서 사용자가 직접 친다.**
  - `MANU` 를 넣고 싶으면 → `MANU_PreDebut_TSR_CT01`
  - 안 넣고 싶으면 → `PreDebut_TSR_CT01`
- 툴은 `{stem}` 이 무엇인지 해석하지 않는다. **그대로 템플릿에 끼워 넣는다.**
- 콘텐츠 타입 약어 매핑은 **보류** (§9 Q2). 매핑이 없어도 stem 자유 입력으로 전부 표현된다.

이렇게 하면 §1.2 의 `MANU_` 편차 문제를 툴이 "정답을 정하는" 방식이 아니라
**"사용자가 한 번 정하고 그 씬 전체에 일관되게 적용되는"** 방식으로 해소한다.
씬 안에서 이름이 갈리는 사고(= 실제로 일어난 `S02` 사고)는 구조적으로 불가능해진다.

#### 설정 파일

```jsonc
{
  "version": 2,
  "name_templates": {
    "master":     "MSEQ_{stem}_{scene}",
    "cut":        "CSEQ_{stem}_{scene}_{cut}",
    "scene_sub":  "SSEQ_{stem}_{scene}_{type}",
    "cut_sub":    "SSEQ_{stem}_{scene}_{cut}_{type}",
    "main_level": "ML_{stem}_{scene}",
    "sub_level":  "SL_{stem}_{scene}_{type}",
    "camera_binding": "{stem}_{scene}_{cut}_camera"
  },
  "scene_format": "S{:02d}",     // → S01
  "cut_format":   "C{:04d}",     // → C0010
  "folders": {
    "scene_sub": "Subsequence", "cut_sub": "Subsequence",
    "map": "Map", "animation": "Animation", "vfx": "VFX"
  },
  "sub_types": [
    {"key": "ANIM",         "folder_color": "#FF604F", "track_color": "#77474B"},
    {"key": "CAM",          "folder_color": "#4DA1FB", "track_color": "#606E94"},
    {"key": "LGT",          "folder_color": "#FFED49", "track_color": "#9C946E"},
    {"key": "VFX",          "folder_color": "#FF9E3B", "track_color": "#997E6D"},
    {"key": "Sound",        "folder_color": "#A14FFF", "track_color": "#745380"},
    {"key": "Media",        "folder_color": "#009416", "track_color": "#6E7F5C"},
    {"key": "LayoutAdjust", "folder_color": "#00BFBA", "track_color": "#498583"}
  ],
  "camera": {
    "float_tracks": [
      {"name": "CurrentFocalLength",  "path": "CurrentFocalLength"},
      {"name": "CurrentAperture",     "path": "CurrentAperture"},
      {"name": "ManualFocusDistance", "path": "FocusSettings.ManualFocusDistance"}
    ]
  },
  "sequence": {"display_rate": 30, "tick_resolution": 24000, "default_cut_frames": 120},

  // 보류 — 정본 확인 후 채운다 (§9 Q2). 비어 있으면 UI 는 stem 자유 입력만 쓴다.
  "content_types": {}
}
```

- 사용자 오버라이드: `<Project>/Config/jun_cinematic_sop.json` 이 있으면 우선한다.
- 프로토타입 D8 (`seq_name.replace("SEQ_cam_", "")` 로 이름 역파싱) 은 **버린다.**
  카메라 바인딩 이름은 `camera_binding` 템플릿으로 **조립**한다. 역파싱은 규칙이 바뀌면 조용히 깨진다.

### 5.3 데이터 모델

```python
CutSpec   = (index: int, start_frame: int, duration_frames: int, name: str)
SceneSpec = (root_path, stem, scene_number, cuts: [CutSpec],
             make_scene_subs, make_cut_subs, make_camera_rig,
             apply_colors, make_side_folders)
```

`project` / `content_type` / `ct` 필드가 rev.1 에 있었으나 **`stem` 하나로 합쳤다** (§5.2 결정).

컷 입력 방식:

| 방식 | 사용처 | Phase |
|------|--------|-------|
| **균등 생성** — 시작번호 / 개수 / 증분 / 컷당 길이 | 프리프로덕션 초기, 컷 길이 미정 | 1 |
| **JSON 컷리스트** — 컷별 길이 지정 | 편집본이 나온 뒤 | 4 |

### 5.4 생성 알고리즘

프로토타입의 단일 패스 루프(282~378줄)를 **계획 / 실행 2단계**로 나눈다. D1·D3 대응.

```
core.build(spec, dry_run):

  # ── 1단계: 계획 (쓰기 없음) ─────────────────────────────
  plan = plan.build_plan(spec)
    for each 대상 (폴더 / 에셋 / 결선 / 컬러):
      EditorAssetLibrary.does_asset_exist()  →  CREATE | SKIP(exists) | CONFLICT(타입 불일치)
  report = plan.summarize()          # "1 MSEQ, 7 scene SSEQ, 13 CSEQ, 91 cut SSEQ / 3 skipped"

  if dry_run:  return report         # 여기서 끝. 아무것도 안 만든다

  # ── 2단계: 실행 ─────────────────────────────────────────
  with unreal.ScopedEditorTransaction("JUN Build Cinematic Sequences"):     # D2
    with unreal.ScopedSlowTask(plan.total, "Building cinematic sequences"): # D4

      A. 폴더 생성                    ensure_directory()            [P4]
      B. SSEQ (leaf) 생성             씬 7개 + 컷 7N개              [P3]
         └ CAM 이고 make_camera_rig 면 → camera.setup(cam_seq, ...) [P6]
      C. CSEQ 생성
         └ 컷 SSEQ 7개를 SubTrack 으로 결선 (트랙 1개당 섹션 1개)   [P5]
         └ 빈 CameraCutTrack 추가
         └ 폴더 7개 + FolderColor                                   (R1)
      D. MSEQ 생성
         └ 씬 SSEQ 7개를 SubTrack 으로 결선                          [P5]
         └ CSEQ N개를 CinematicShotTrack 에 누적 오프셋으로 배치     (D6/D7)
         └ PlaybackRange = 0 ~ 총 길이, DisplayRate 설정
      E. 저장: 생성한 에셋만 save_asset()                            (D5)

  return report
```

**순서가 중요하다** — leaf(SSEQ) → CSEQ → MSEQ. 참조가 아래에서 위로 흐른다.

**프레임 배치 (D6 수정)**

```python
# 프로토타입: 전부 set_range(0, duration)  ← 마스터에서 컷이 전부 겹친다
# 수정:
offset = 0
for cut in spec.cuts:
    shot_section = shot_track.add_section()
    shot_section.set_sequence(cseq)
    shot_section.set_range(offset, offset + cut.duration_frames)
    offset += cut.duration_frames
# CSEQ 내부의 서브 7개는 0 ~ duration (컷 로컬 시간) 유지 — 이건 프로토타입이 맞다
```

**트랙 1개당 섹션 1개** — 프로토타입 161줄이 루프 안에서 트랙을 새로 만드는 것은 의도된 설계다.
한 `SubTrack` 에 7개 섹션을 넣으면 시간축에서 겹쳐 하나만 평가된다.
(대안: 한 트랙 + `set_row_index()` 로 행 분리. §7 A9 에서 실측 후 결정)

**비파괴 보장 (D1)**
- 생성 전 전수 `does_asset_exist()` 확인
- 이미 있으면 생성은 건너뛰되 **결선은 시도한다** (누락분만 채우는 "보수" 동작)
- 이미 결선된 섹션은 다시 붙이지 않는다 (`track.get_sections()` → `get_sequence()` 대조)

### 5.5 Validate 모드

선택한 `S##` 폴더를 훑어 SOP 규격과 대조하고 리포트만 낸다. **아무것도 쓰지 않는다.**
Stem 이 자유 입력이므로, Validate 는 **씬 안에서 stem 이 일관된지**를 본다 (정답 stem 을 강요하지 않는다).

| 검사 | 예 (실제 발견된 것) |
|------|---------------------|
| **씬 내 stem 불일치** | `S02` 폴더에 `MSEQ_MANU_PreDebut_CT01_...` 과 다른 stem 이 섞임 |
| 폴더명과 에셋 내 씬 번호 불일치 | `S02` 폴더 안에 `..._S01_...` 에셋 |
| SSEQ 7종 누락 | |
| MSEQ 에 미결선된 CSEQ | |
| CSEQ 에 미결선된 SSEQ | |
| 컬러코드 미적용 폴더 | |
| 잔여물 | `UE_Placeholder.uasset`, 규격 외 변종(`..._Full`) |

리포트는 Output Log(`LogPython`) + 선택적으로 `Saved/JUNTools/cinematic_validate_<scene>.csv`.

### 5.6 UI — 사용자 입력 중심 (rev.2 전면 개정)

`unreal.EditorDialog.show_object_details_view()` — 모달 디테일 뷰 (A00510 과 동일 패턴).

```
JUN Cinematic Sequence Builder
├─ Target
│   Root Path              /Game/MANUCinematic/PreDebut/Teaser/CT01   (읽기 전용, 자동 획득)
│                            ↑ 콘텐츠 브라우저 선택 폴더에서 가져옴 [P2]
│   Name Stem              [ PreDebut_TSR_CT01                     ]  ★ 자유 텍스트
│                            ↑ MANU 를 넣고 싶으면 직접 입력:
│                              MANU_PreDebut_TSR_CT01
│   Scene Number           [ 6 ]                        → S06
├─ Cuts
│   Cut Start              [ 10 ]                       → C0010
│   Cut Count              [ 13 ]
│   Cut Step               [ 10 ]
│   Frames Per Cut         [ 120 ]
│   Display Rate (fps)     [ 30 ]
├─ Options
│   [x] Create Scene Subsequences        (7 types)
│   [x] Create Cut Subsequences          (7 types per cut)
│   [x] Set Up CineCamera in CAM         ← 프로토타입 P6
│   [x] Apply SOP Folder Colors
│   [x] Create Map / Animation Folders
└─ [x] Dry Run First (recommended)
```

**Name Stem 이 이 UI 의 핵심이다.**

- 툴은 stem 을 해석하지 않는다. 입력된 문자열이 `MSEQ_{stem}_{scene}` 에 그대로 들어간다.
- 마지막 입력값을 `Saved/JUNTools/a00520_last.json` 에 기억해 다음 실행 시 기본값으로 채운다.
  같은 CT 의 다음 씬을 만들 때 다시 타이핑하지 않게 하려는 것이고, **씬 간 stem 일관성**도 자연히 따라온다.
- 빈 문자열 / 공백 / 슬래시 / 언리얼 금지 문자는 `spec.validate()` 에서 거부한다.

**2단계 확인 흐름** (모달 디테일 뷰가 실시간 미리보기를 못 하는 제약 — 가이드 §10 — 을 우회)

```
① show_object_details_view()  → 사용자가 값 입력, OK
② Dry Run 실행 → Output Log 에 전체 계획 출력
     Will create under /Game/.../CT01/S06 :
       MSEQ_PreDebut_TSR_CT01_S06
       SSEQ_PreDebut_TSR_CT01_S06_{ANIM,CAM,LGT,VFX,Sound,LayoutAdjust,Media}
       CSEQ_PreDebut_TSR_CT01_S06_C0010 ... _C0130   (13)
       SSEQ_..._C0010_{7종} ...                      (91)
       ─ total 112 assets, 0 skipped, 0 conflicts
③ show_message("Create 112 assets?", OK/Cancel)   ← 이름을 눈으로 확인하고 결정
④ OK 면 실제 생성
```

`Dry Run First` 를 끄면 ②③ 을 건너뛴다. **기본은 켜짐.**

**메뉴 항목 2개** (registry `SECTION_ORDER` 에 `"Cinematic"` 추가):

| 섹션 | 항목 | 동작 |
|------|------|------|
| Cinematic | `Cinematic Sequence Builder...` | 위 다이얼로그 |
| Cinematic | `Validate Cinematic Structure` | 콘텐츠 브라우저에서 선택한 `S##` 폴더를 검사 |

- **UI 문자열은 전부 영어** (가이드 §4 / CLAUDE.md §4).

### 5.7 프로토타입 → 본 툴 이식 매핑

| 프로토타입 | 이식 위치 | 변경 |
|-----------|----------|------|
| `_call_first_working`, `add_master_track_compat`, `add_possessable_compat`, `add_binding_track_compat`, `set_binding_parent_compat`, `remove_binding_compat` | `compat.py` | **거의 그대로.** 에러 메시지를 영어로, 후보 목록에 5.8 대비 여지 |
| `ensure_directory`, `create_level_sequence` | `build.py` | `does_asset_exist()` 사전 확인 추가 (D1) |
| `get_root_path_from_content_browser` | `ui.py` | 그대로. UI 의 Root Path 자동 획득 |
| `add_sub_sequences_to_parent` | `build.py` | 3종 → 7종, 프레임 오프셋 인자화 (D6) |
| `setup_cam_sequence_with_cine` | `camera.py` | 이름 역파싱 제거 → 템플릿 조립 (D8), `EditorLevelLibrary` → `EditorActorSubsystem` 폴백 (D9), float 트랙 목록을 JSON 화 |
| `generate_sequences_for_shots` | `plan.py` + `build.py` | 계획/실행 분리, 3계층화, 트랜잭션·진행률·부분 저장 (D2·D3·D4·D5·D7) |
| `save_all_under` | `build.py` | `save_directory(recursive)` → 생성 목록만 `save_asset()` (D5) |

원본 `seq_batch_tool_ue57.py` 는 **`Docs/Plans/` 에 참고 자료로 그대로 보존**한다. 코드 이식 후에도 지우지 않는다.

---

## 6. 단계별 구현 계획

프로토타입 덕분에 rev.1 의 Phase 0 이 절반으로 줄었다.

| Phase | 산출물 | 검증 | 예상 |
|-------|--------|------|------|
| **0. 잔여 API 검증** | `Docs/verify/verify_sequencer_api.py` — **미확인 3건만** (폴더 컬러 / 트랙 틴트 / CinematicShotTrack) + 5.7 재확인 | 커맨드렛 로그 | **0.25d** (rev.1: 0.5d) |
| **1. compat + 코어** | `compat.py`(P1 이식) · `naming.py` · `spec.py` · `plan.py` · `build.py`. Dry-run 포함, 컬러/카메라 없이 3계층 생성·결선 | 스크래치 프로젝트에 1개 씬 생성 후 에디터에서 MSEQ 열어 육안 확인 | 1.5d |
| **2. 카메라 + 컬러** | `camera.py`(P6 이식 + D8/D9 수정) · 폴더 컬러 · 트랙 틴트 | 생성된 CAM SSEQ 를 실측 `..._C0010_CAM.uasset` 과 구조 대조 | 1d |
| **3. Validate** | `validate.py` + CSV 리포트 | 실제 `Teaser/CT01/S02` 에 걸어 §1.2 사고가 검출되는지 확인 | 0.75d |
| **4. UI + 문서** | `ui.py`(2단계 확인 흐름) · registry 등록 · `Docs/Tools/A00520_*.md` · CHANGELOG · version | 메뉴에서 실행 | 1d |
| **5. (선택) 확장** | JSON 컷리스트 · ML/SL 레벨 생성 · 중간 컷 삽입(`C0155`) 지원 | | 1d+ |

**합계 4.5일 (Phase 5 제외).**
Phase 1 완료 시점에 이미 실무 투입 가능하다 (UI 없이 커맨드렛/콘솔 호출).

---

## 7. 검증 계획 — 추측하지 않는다

가이드 §2 원칙대로 **헤드리스 커맨드렛으로 확인**한 뒤 코드를 쓴다.

```bash
UnrealEditor-Cmd.exe <Scratch>.uproject -run=pythonscript \
  -script="Docs/verify/verify_sequencer_api.py" -unattended -nosplash -nullrhi \
  -AbsLog="verify_sequencer.log"
```

### 상태표 — 프로토타입이 무엇을 이미 답했는가

| # | 항목 | 상태 | 근거 / 대안 |
|---|------|------|------------|
| A1 | `create_asset(..., LevelSequence, LevelSequenceFactoryNew())` | ✅ **검증됨** | 프로토타입 23~33줄 |
| A2 | 마스터 트랙 추가 (`add_master_track` / `Extensions.add_master_track` / `add_track`) | ✅ **검증됨 (폴백 필요)** | 프로토타입 82~98줄. **5.7 에서 바인딩이 갈린다는 것 자체가 확인된 사실** |
| A3 | `sub_section.set_sequence()` + `set_range(a, b)` | ✅ **검증됨** | 프로토타입 164~170줄 |
| A4 | `add_spawnable_from_instance` / `get_binding_id` / `set_camera_binding_id` | ✅ **검증됨** | 프로토타입 197~217줄 |
| A5 | `MovieScenePropertyTrackExtensions.set_property_name_and_path` | ✅ **검증됨** | 프로토타입 231~235줄 |
| A6 | `EditorUtilityLibrary.get_selected_folder_paths` / `get_current_content_browser_path` | ✅ **검증됨** | 프로토타입 48~58줄 |
| A7 | `EditorAssetLibrary.make_directory` / `does_directory_exist` / `save_directory` | ✅ **검증됨** | 프로토타입 16~38줄 |
| **A8** | **`unreal.MovieSceneCinematicShotTrack` + 섹션에 `set_sequence()`** | ❓ **미확인** | 프로토타입이 안 쓴다(D7). 안 되면 `SubTrack` 으로 대체 — 실측 MSEQ 와 구조가 달라지므로 사용자 확인 필요 |
| **A9** | **`MovieSceneFolder` 생성 + 폴더 컬러 지정** | ❓ **미확인 (R1)** | 안 되면 컬러 적용을 **선택 기능으로 격하**하고 문서에 명시 |
| **A10** | **트랙 틴트(`TrackTint`) 지정** | ❓ **미확인 (R2)** | 동일 |
| A11 | 한 `SubTrack` 에 `set_row_index()` 로 7섹션 분리 vs 트랙 7개 | ❓ 미확인 | 안 되면 프로토타입 방식(트랙 7개) 유지 — 이미 검증됨이라 무위험 |
| A12 | `EditorActorSubsystem.spawn_actor_from_class` (D9) | ❓ 미확인 | 안 되면 `EditorLevelLibrary` 유지 (프로토타입에서 동작 확인됨, deprecated 경고만) |
| A13 | `ScopedEditorTransaction` 안에서 에셋 생성이 롤백되는가 | ❓ 미확인 | 롤백 안 되면 실패 시 "생성된 목록"을 로그로 뱉고 수동 정리 안내 |
| A14 | `MovieSceneSequenceExtensions.remove_binding` 존재 | ⚠️ **없을 수 있음** | 프로토타입 133~141줄이 이미 폴백 + 경고 처리. 그대로 이식 |

**미확인은 A8~A13 여섯 건뿐이고, 그중 A9/A10 둘만 실질 위험이다.**

### 위험도

| 위험 | 영향 | 완화 |
|------|------|------|
| **A9/A10 컬러 API 부재** | SOP §9 컬러코드 미충족 | 기능 격하 + 문서화. C++ 로 뚫는 건 이식성을 버리는 선택이라 하지 않는다 (가이드 §3①) |
| **A8 ShotTrack 부재** | MSEQ 구조가 실측과 달라짐 | SubTrack 폴백 + **사용자에게 알리고 결정 요청** (조용히 다른 구조를 만들지 않는다) |
| 대량 생성 중 에디터 정지 | 568개 생성 시 수 분 | `ScopedSlowTask` 진행률 + 취소 (D4) |
| CAM 셋업의 임시 액터 잔류 | 레벨이 더러워짐 | 프로토타입 255줄 `destroy_actor` + `try/finally` 로 감쌈 |
| 빈 바인딩 잔류 (빨간 바인딩) | 시퀀서에 쓰레기 | A14 폴백 + 경고 (프로토타입과 동일) |
| 리디렉터 발생 | 참조 깨짐 | 툴은 리네임/이동을 하지 않으므로 해당 없음 |
| `.uasset` 이 저장소에 대량 유입 | JUN_UE 는 코드 저장소 | **JUN_UE 에는 에셋을 만들지 않는다.** 검증은 스크래치 프로젝트에서 (가이드 §2) |

---

## 8. 운영 · 파이프라인 고려사항

| 항목 | 내용 |
|------|------|
| **SVN** | `Content/MANUCinematic` 은 **별도 SVN 리포**다 (SOP 007 §4.1). 툴이 만든 수백 개 에셋은 사용자가 직접 `svn add` 해야 한다. → 실행 후 로그에 `N assets created — remember to add them to SVN` 을 남긴다. 툴은 SVN 을 절대 호출하지 않는다 |
| **커밋 단위** | 씬 하나 단위로 생성 → 커밋 권장. 태그 예: `[신규] 시네마틱 CT01 S06 시퀀서 구조 생성` |
| **플러그인 배치** | `MANUProject` 는 SVN+Git 이중 관리라 `Plugins/` 아래에 두면 딸려 올라간다 → **`UE_ADDITIONAL_PLUGIN_PATHS` 환경변수 방식**을 쓴다 (가이드 §6 방법 A) |
| **협업 충돌** | 두 사람이 같은 씬에 동시에 돌리면 안 된다. Validate 를 먼저 돌려 확인 |
| **기존 씬 보수** | 이미 만들어진 S01~S05 에 툴을 돌리면 **누락분만 채운다**. 잘못된 이름은 고치지 않는다 (§3.2) |
| **CAM 셋업 옵션** | 이미 아티스트가 카메라를 만든 CAM SSEQ 에는 `Set Up CineCamera` 를 **끄고** 돌려야 한다. 툴은 기존 CAM SSEQ 를 건너뛰므로 자동으로 안전하지만, 로그에 명시 |

---

## 9. 착수 전 확인이 필요한 항목

| # | 질문 | 상태 |
|---|------|------|
| **Q1** | 마스터 이름에 `MANU_` 를 넣는가? | ✅ **해결 (rev.2).** 코드에 넣지 않는다. **UI 의 `Name Stem` 텍스트 필드에 사용자가 직접 입력**한다 (§5.2, §5.6) |
| **Q2** | 콘텐츠 타입 약어 정본 (`Teaser`→`TSR`, `ShortForm`→`SHF`, …) | ⏸ **보류 — 사용자가 정본 확인 중.** 그동안 `content_types` 는 빈 채로 두고 stem 자유 입력으로 우회한다. 정본이 나오면 JSON 만 채우고, 원하면 UI 에 드롭다운을 추가한다 (코드 변경 없음) |
| **Q3** | 빈 폴더(`VFX/`, `Animation/`)를 `UE_Placeholder` 로 유지하는가 | ❓ 미결. 언리얼은 빈 폴더를 저장하지 않는다. 실제로 `S05` 등에 `UE_Placeholder.uasset` 이 존재. **옵션으로 두되 기본 끄기** |
| **Q4** | 기본 컷 길이 / 프레임레이트 | ❓ 미결. 잠정 30fps / 120프레임(4초). 프로토타입 기본값은 100프레임. UI 에서 입력 가능하므로 위험 낮음 |
| **Q5** | `S02` 의 `_Full` 마스터(`MSEQ_MANU_PreDebut_CT01_S01_Full`)는 무엇인가 | ❓ 미결. 규격에 없는 변종. **범위 밖**으로 두고 Validate 에서 `unknown asset` 으로만 보고 |
| **Q6** | 잘못된 `S02` 네이밍을 지금 고칠 것인가 | ❓ 미결. 참조가 걸려 있어 리네임은 별개 작업. 이 툴 범위 밖. Validate 리포트 제출 후 별도 판단 |
| **Q7** | CAM 자동 셋업의 기본 카메라 값 (초점거리 / 조리개 / 센서) | ❓ 신규. 프로토타입은 트랙만 만들고 값은 기본값. 팀 표준이 있으면 JSON 에 넣는다 |

**Q1 해결 · Q2 보류 상태로 Phase 0~1 착수가 가능하다.** Q2 는 stem 자유 입력이 우회하므로 블로커가 아니다.

---

## 10. 완료 정의 (DoD)

- [ ] Phase 0 검증 스크립트가 헤드리스로 통과하고, A8~A13 결과가 `Docs/Tools/A00520_*.md` 에 **실측으로** 기록됨
- [ ] 빈 씬 폴더에 툴을 돌려 `MSEQ + 7 + N + 7N` 이 생성되고, **에디터에서 MSEQ 를 열면 컷과 서브가 전부 보인다**
- [ ] MSEQ 타임라인에서 **컷이 겹치지 않고 순차 배치**된다 (D6 수정 확인)
- [ ] 생성된 CAM SSEQ 의 구조가 실측 `SSEQ_..._C0010_CAM.uasset` 과 일치한다 (스포너블 + CameraCut + Transform + Float ×3)
- [ ] 같은 씬에 두 번 돌려도 **에셋이 중복 생성되지 않고 아무것도 깨지지 않는다** (멱등성 — D1)
- [ ] Dry Run 이 실제 생성과 동일한 목록을 리포트한다 (D3)
- [ ] `Name Stem` 에 `MANU_PreDebut_TSR_CT01` 을 넣으면 그대로, 빼면 뺀 대로 생성된다 (§5.2)
- [ ] Validate 가 실존하는 `Teaser/CT01/S02` 의 stem/씬번호 불일치를 검출한다
- [ ] 생성 도중 취소하면 레벨에 임시 `CineCameraActor` 가 남지 않는다
- [ ] `Docs/Tools/A00520_CinematicSequenceBuilder.md` · `CHANGELOG.md` · `version.py` 갱신
- [ ] `registry.py` 에 `Cinematic` 섹션 + 항목 2개 등록, Reload 후 메뉴 중복 없음

---

## 부록 A. 조사에 사용한 명령

```bash
# 구조 파악
find "MANUProject/Content/MANUCinematic/PreDebut/Teaser" -type d | grep -v _Subscenes

# 기존 툴 부재 확인
grep -rliE "LevelSequenceFactoryNew|MovieSceneSubSection|MovieSceneCinematicShotTrack|create_level_sequence" \
     Tools src MANUProject/Source MANUProject/Plugins

# 시퀀서 에셋 내부 결선 확인 (바이너리에서 ASCII 문자열 추출)
python -c "import re; d = open('MSEQ_PreDebut_TSR_CT01_S01.uasset','rb').read(); \
print(chr(10).join(sorted({x.decode() for x in set(re.findall(rb'[ -~]{5,}', d))})))"
```

## 부록 B. 참조

- [`seq_batch_tool_ue57.py`](seq_batch_tool_ue57.py) — **프로토타입.** UE 5.7 바인딩 검증 자산 (§1.4)
- `C:\MANUSetup\docs\DnableSOP\007 Cinematic\001 Key Base.md` — **정본 스펙**
- `C:\MANUSetup\docs\DnableSOP\006 SetDressing\002 Cinematic.md` — 서브레벨 · LayoutAdjust
- `C:\MANUSetup\docs\DnableSOP\002 Common\008 Prefix Suffix Rules.md` §1.4 — 시네마틱 Prefix (잠정)
- [`JUN_UE/Docs/00_UE_Tool_Plugin_Guide.md`](../00_UE_Tool_Plugin_Guide.md) — 설계 근거 · 함정
- 실측 대상: `MANUProject/Content/MANUCinematic/PreDebut/Teaser/CT01/S01`

---

## 부록 C. 개정 이력

| rev | 날짜 | 내용 |
|-----|------|------|
| 1 | 2026-08-24 | 최초 작성. 기존 툴 부재 확인, 실측 구조 분석, 설계 |
| **3** | **2026-08-24** | **구현 완료.** 계획대로 `compat / naming / spec / plan / camera / build / validate / core / ui` 9개 모듈 + `Config/jun_cinematic_sop.json` + `Docs/verify/verify_sequencer_api.py` 작성. registry 에 `Cinematic` 섹션 + 항목 2개 등록. `.uplugin` 에 `SequencerScripting` 의존 추가. 계획 대비 변경 두 가지: ① 이미 존재하는 마스터의 재생 범위·프레임레이트는 덮어쓰지 않고 경고만 남긴다(아티스트 작업 보호) ② 저장을 `우리가 만들었거나 결선한 에셋`으로 좁혔다(불필요한 SVN 수정 방지). **Phase 0 실측은 미완** — §7 A8/A9/A10 은 여전히 미확인이고 폴백만 넣어 둔 상태 |
| **2** | **2026-08-24** | **프로토타입 `seq_batch_tool_ue57.py` 반영** — §1.4 신설(이식 자산 P1~P6 / 결함 D1~D11), CAM 자동 셋업을 목표로 승격(§3.1-6), `compat.py`·`camera.py`·`plan.py` 모듈 분리(§5.1), 이식 매핑표(§5.7), 검증 항목 대부분 ✅ 로 전환(§7), Phase 재조정(§6). **네이밍: `MANU_` 하드코딩 폐기 → UI `Name Stem` 자유 입력(§5.2·§5.6, Q1 해결).** 약어 매핑 Q2 보류 처리 |
