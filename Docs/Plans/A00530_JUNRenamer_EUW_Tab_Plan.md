# A00530 — JUN Renamer · EUW 탭 전환 작업 계획서

> 모달 다이얼로그를 **도킹되는 에디터 탭(Editor Utility Widget)** 으로 바꿔서,
> 창을 띄운 채로 **콘텐츠 브라우저를 클릭할 수 있게** 한다.

- **작성일**: 2026-11-20
- **작성자**: Ji Hun Park (Junny)
- **대상 저장소**: `JUN_UE` (플러그인 `JUNTools`)
- **대상 툴**: `A00530_jun_renamer` (현재 툴 v01.00 / 플러그인 v01.04)
- **상태**: **구현 완료 (2026-11-20)** — P1~P6 완료, 헤드리스 5.4 · 5.7 43/43. **P7(에디터 눈 확인) 남음**
- **결정**: 탭 제목 A(에셋 `Tab Display Name = JUN Renamer`) · 자동 불러오기는 목록이 비었을 때만 · 모달 대체 경로 유지
- **관련 문서**: [../Tools/A00530_JUNRenamer.md](../Tools/A00530_JUNRenamer.md) §7 (모달 제약)

---

## 0. 요약

| 항목 | 결론 |
|------|------|
| 최우선 목표 | 창이 떠 있는 동안 **콘텐츠 브라우저를 클릭할 수 있어야 한다** |
| 방법 | EUW 탭 안의 `DetailsView` 위젯에 **지금의 설정 오브젝트(`JUNRenamerSettings`)를 그대로 연결** |
| 바뀌는 코드 | 사실상 `ui.py` 의 **창을 띄우는 부분**뿐. `naming.py` · `convention.py` · `core.py` 는 그대로 |
| 덤으로 얻는 것 | 값을 고치면 **미리보기 자동 갱신** (`DetailsView.on_property_changed`) |
| 지원 엔진 | **UE 5.4 이상** — EUW 를 5.4 로 저장했고, 기존 로직도 5.4 / 5.5 / 5.7 에서 31/31 |
| 에셋 | `/JUNTools/A00530_jun_renamer/EUW_JUNRenamer` (사용자 제작, 확인 완료) |
| 안전망 | EUW 를 못 찾거나 탭을 못 띄우면 **지금의 모달 창으로 자동 대체** |

---

## 1. 배경

현재 창은 `unreal.EditorDialog.show_object_details_view()` 로 띄운다. 이 함수는 엔진 안에서
`GEditor->EditorAddModalWindow()` 를 부르는 **모달 창**이라, 떠 있는 동안 다른 에디터 창을 누를 수 없다.
그래서 v01.00 은 우회책을 넣었다 — 열 때 선택 자동 불러오기, 창을 닫아도 남는 입력값,
"Base 고르고 열기 → 닫기 → Targets 고르고 다시 열기" 흐름. 쓰기 불편하다.

파이썬에는 모덜리스 Slate 창을 만드는 API 가 없다. 대신 **EUW 는 레벨 에디터의 일반 도킹 탭**이라
모달이 아니다. EUW 안에 넣을 수 있는 `DetailsView` 위젯은 지금 다이얼로그와 **같은 디테일 패널**이므로,
설정 클래스 · `CallInEditor` 버튼 · 미리보기 배열을 그대로 재사용할 수 있다.

---

## 2. 확인된 사실 (2026-11-20)

| 사실 | 근거 |
|------|------|
| EUW 에셋 로드 · 부모 `EditorUtilityWidget` · 루트 위젯 = `DetailsView` 하나 · 변수로 노출 | 헤드리스 로드 — 5.4.4 / 5.5.4 / 5.7.4(MANU) 모두 |
| 에셋 저장 버전 = `++UE5+Release-5.4` | `.uasset` 헤더 |
| `DetailsView.set_object()` · `on_property_changed` 존재 | 3 개 엔진 파이썬 API |
| `EditorUtilitySubsystem.spawn_and_register_tab()` · `does_tab_exist()` · `close_tab_by_id()` · `find_utility_widget_from_blueprint()` 존재 | 3 개 엔진 파이썬 API |
| 탭 ID = `<에셋 경로>_ActiveTab`. 같은 에셋으로 다시 부르면 **새 탭을 만들지 않고 기존 탭을 띄운다** | `EditorUtilitySubsystem.cpp` `RegisterTabAndGetID` (`HasTabSpawner` 검사) |
| 탭 제목 = EUW 의 `Tab Display Name`(Class Defaults). 비어 있으면 에셋 이름을 풀어 쓴 것(`EUW JUNRenamer`) | `EditorUtilityWidgetBlueprint.cpp` `GetTabDisplayName()` |
| CallInEditor 버튼은 **모든 디테일 패널**에 붙는다 (`FObjectDetails` 가 "Object" 에 전역 등록) | `DetailCustomizations` 소스 |
| 디테일 패널은 틱마다 배열 크기 변화를 보고 다시 그린다 | `FPropertyNode::EnsureDataIsValid()` |
| 헤드리스(커맨드렛)에서는 **탭을 아예 등록하지 않는다** | `RegisterTabAndGetID` 의 `!IsRunningCommandlet()` |
| 기존 Renamer 로직 · 플러그인 로드 | `verify_a00530_renamer.py` 5.4 / 5.5 / 5.7 모두 31/31 |

---

## 3. 설계

### 3.1 흐름

```
Tools > JUN > Asset > JUN Renamer...
  └ ui.show()
      ├ EUW 로드 (/JUNTools/A00530_jun_renamer/EUW_JUNRenamer)
      ├ EditorUtilitySubsystem.spawn_and_register_tab(EUW)     ← 이미 열려 있으면 그 탭을 앞으로
      ├ 탭 위젯.DetailsView.set_object(설정 오브젝트)          ← 세션에 하나뿐인 오브젝트
      ├ DetailsView.on_property_changed 에 콜백 연결 (중복 연결 방지)
      └ (실패 시) show_modal()  = 지금의 모달 다이얼로그
```

### 3.2 설정 오브젝트의 수명

- 탭은 열려 있는 동안 계속 같은 오브젝트를 보여 준다 → 오브젝트를 **세션에 하나만** 만든다.
- 보관 위치를 `jun_tools.tools.__dict__` 에서 **`sys.modules["_jun_tools_session"]`**(jun_tools 밖의 빈 모듈)로 옮긴다.
  - 이유: `Reload JUN Tools` 는 `jun_tools*` 를 전부 비운다. 그때 uclass 가 다시 등록되면, 탭이 붙잡고 있는
    이전 인스턴스가 재인스턴싱되며 ensure 가 난다(v01.00 에서 실측한 그 문제). 세션 모듈에 두면
    `Reload JUN Tools` 뒤에도 클래스 · 오브젝트 · 입력값이 그대로 남는다.
  - 대가: 프로퍼티나 버튼 **구성**을 바꾸면 에디터를 재시작해야 반영된다(코드 수정은 리로드로 반영 — 지금과 같다).
- 지금의 "값 저장/복원(`_save_state` / `_restore_state`)"은 오브젝트가 계속 살아 있으므로 필요 없어진다.
  모달 대체 경로도 같은 오브젝트를 쓴다.

### 3.3 실시간 미리보기

- `on_property_changed(property_name)` 를 받아:
  - Assets / Rename 칸이 바뀌면 → `preview_rename()`
  - Copy Name 칸이 바뀌면 → `preview_copy()`
  - 미리보기 배열 · `Loaded` 칸 자체가 바뀐 것은 무시(되먹임 방지)
- 엔진은 이 이벤트를 **편집이 끝났을 때**(Enter · 포커스 이동 · 체크 · 드롭다운 선택) 보낸다 —
  글자마다 계산하지 않는다.
- 콜백도 버튼처럼 `_ui()` 로 **최신 모듈**의 함수를 부른다(DEV_MODE 리로드 반영).
- `Preview` / `Preview Copy` 버튼은 남긴다 — 콘텐츠 브라우저에서 이름이 바뀌는 등 **칸 밖의 변화**를 다시 반영할 때 쓴다.

### 3.4 모달 시절 우회책 정리

| 우회책 | 처리 |
|--------|------|
| 창을 열 때 콘텐츠 브라우저 선택을 자동으로 불러오기 | **목록이 비어 있을 때만** 불러온다 (이미 불러온 목록을 덮어쓰지 않는다) |
| "Close this window, select assets, then open it again." 경고 | "Select assets in the Content Browser first." 로 |
| 창을 닫아도 값이 남게 하는 저장/복원 | 삭제 (§3.2) |
| OK / Cancel 처리 | 탭에는 없다. 모달 대체 경로에만 남긴다 |
| 툴 문서 §7 "제약" 표 | 모달 · 미리보기 항목 삭제, EUW 버전 주의 추가 |

### 3.5 탭 제목

두 방법 중 하나 — **§8 결정 1**.

| 방법 | 내용 | 비고 |
|------|------|------|
| A. 에셋에서 설정 (추천) | 5.4 에디터에서 EUW 를 열고 Class Defaults > `Tab Display Name` = `JUN Renamer` | 한 번만 하면 끝. 코드 없음 |
| B. 코드에서 설정 | 탭을 띄우기 전에 CDO 의 `tab_display_name` 을 메모리에서만 바꾼다 | 에셋이 더티로 표시돼 종료 시 저장을 묻고, **5.7 에서 저장하면 5.4 에서 못 연다** — 피하고 싶다 |
| (그대로) | `EUW JUNRenamer` 로 보인다 | 기능에는 영향 없음 |

---

## 4. 변경 파일

| 파일 | 내용 |
|------|------|
| `Content/Python/jun_tools/tools/A00530_jun_renamer/ui.py` | `show()` = EUW 탭 · `show_modal()` = 기존 다이얼로그(대체) · 세션 모듈 · 속성 변경 콜백 · 우회책 정리 |
| `Content/Python/jun_tools/tools/A00530_jun_renamer/core.py` | 경고 문구만 (모달 안내 삭제) |
| `Content/A00530_jun_renamer/EUW_JUNRenamer.uasset` | **처음 커밋** (사용자 제작, 5.4) |
| `Content/Shared/README.md` | 빈 폴더를 git 에 남기기 위한 설명 파일 (공용 에셋 규칙) |
| `Docs/verify/verify_a00530_renamer.py` | EUW 로드 · 위젯 구조 · 탭 경로 대체 동작 · 속성 변경 콜백 검사 추가 |
| `Docs/Tools/A00530_JUNRenamer.md` | 쓰는 법(Copy Name 흐름 단순화) · 실시간 미리보기 · 제약 · 5.4 저장 규칙 |
| `CLAUDE.md` §1 구조 | `Content/<툴 폴더>/` · `Content/Shared/` 에셋 규칙 추가 |
| `CHANGELOG.md` · `Docs/WORKLOG.md` · `version.py` · `.uplugin` | 플러그인 v01.05, 툴 v01.01 |
| `.claude/memory/` | EUW + DetailsView 패턴, 에셋은 5.4 에서 저장 규칙 |

`naming.py` · `convention.py` · `registry.py` · 메뉴는 바뀌지 않는다.

---

## 5. 작업 단계

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| P1 | 세션 모듈로 클래스 · 오브젝트 보관 이전, `_save_state` / `_restore_state` 제거 | 기존 검증 31/31 유지 |
| P2 | `show()` → EUW 탭, 기존 다이얼로그는 `show_modal()` 로 이름만 바꿔 대체 경로로 | 헤드리스에서 대체 경로로 정상 종료 |
| P3 | `on_property_changed` 콜백 · 중복 연결 방지 · 되먹임 무시 | 콜백 직접 호출 시 미리보기 갱신 |
| P4 | 우회책 정리 (§3.4) | 문구 · 동작 확인 |
| P5 | 검증 스크립트 보강 → **5.4 · 5.7 헤드리스** 실행 | 전부 통과 |
| P6 | 문서 · 버전 · 메모리 갱신, **로컬 커밋** (푸시는 요청 시) | — |
| P7 | **에디터에서 눈으로 확인** (사용자) — §6.2 체크리스트 | 1 번 항목 통과 |

---

## 6. 검증

### 6.1 헤드리스 (5.4 · 5.7)

증명할 수 있는 것: EUW 로드 · 위젯 구조, 설정 오브젝트를 `DetailsView` 템플릿에 `set_object` 할 수 있음,
속성 변경 콜백이 맞는 미리보기를 다시 계산함, 탭을 못 띄우는 환경에서 모달로 대체됨, 세션 오브젝트가
리로드 뒤에도 같은 것임, 기존 31 항목.

증명할 수 없는 것: **탭이 실제로 뜨는지, 콘텐츠 브라우저를 누를 수 있는지, 버튼이 보이는지** —
커맨드렛은 탭을 등록하지 않는다(§2). → 6.2 로 확인한다.

### 6.2 에디터 체크리스트 (사용자)

1. **탭이 떠 있는 상태로 콘텐츠 브라우저에서 에셋을 클릭 · 선택할 수 있다** ← 최우선
2. 탭이 레벨 에디터에 도킹된다 · 메뉴를 다시 눌러도 탭이 하나만 있다
3. Assets / Rename / Copy Name 칸과 버튼(`Load Selected`, `-1 Front`, `Rename`, `Base <- Selection` …)이 보인다
4. 칸을 고치고 Enter → `Rename Preview` 가 저절로 바뀐다
5. 콘텐츠 브라우저에서 선택을 바꾼 뒤 `Load Selected` / `Base <- Selection` 이 **새 선택**을 가져온다
6. `Rename` / `Copy Name` 이 실제로 이름을 바꾸고 확인 창이 뜬다
7. 탭을 닫았다 다시 열면 입력값이 남아 있다

---

## 7. 위험과 대응

| 위험 | 대응 |
|------|------|
| 탭 안에서 CallInEditor 버튼이 안 보인다 | 소스상 모든 디테일 패널에 붙지만 화면 확인 전까지는 가정이다. 안 보이면 EUW 에 버튼 위젯을 직접 추가해야 한다(에셋 작업 — 사용자) |
| `on_property_changed` 가 파이썬 콜백을 받지 못한다 | 버튼 방식(`Preview`)이 그대로 남아 있어 기능은 유지된다 |
| 탭을 닫으면 위젯이 사라져 이전 콜백이 남는다 | 콜백은 위젯이 아니라 함수에 묶고, 열 때마다 현재 위젯에 다시 연결(중복 검사) |
| EUW 를 5.5+ 에디터에서 저장해 5.4 에서 못 연다 | 문서 · `CLAUDE.md` 에 "EUW 는 5.4 에서 저장" 명시. 코드는 실패 시 모달로 대체 |
| 프로퍼티 구성 변경이 리로드로 반영되지 않는다 | 에디터 재시작 필요 — 문서에 적는다 (§3.2) |

---

## 8. 결정이 필요한 것

1. **탭 제목** — A(에셋에서 `Tab Display Name = JUN Renamer`, 추천) / B(코드) / 그대로(`EUW JUNRenamer`)
2. **열 때 선택 자동 불러오기** — 목록이 비어 있을 때만(추천) / 아예 없애기
3. **모달 대체 경로** — 남기기(추천: EUW 가 없거나 깨져도 툴이 열린다) / 없애기

---

## 9. 범위 밖

- 공용 호스트 EUW(`Shared/EUW_JUNDetailsHost`)로 여러 툴을 띄우는 구조 — 이번 결과(특히 탭 제목 · 탭 ID)를 보고 다음 툴에서 판단
- 다른 툴(A00510 · A00520)의 EUW 전환
- 미리보기를 표(색 · 열)로 바꾸기 — EUW 에 리스트 위젯을 넣어야 해서 에셋 작업이 따로 필요
