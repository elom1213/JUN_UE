# A00530 — JUN Renamer

콘텐츠 브라우저 에셋의 **이름을 일괄 변경**한다. 미리보기로 결과를 먼저 보고 버튼으로 실행한다.

- **버전**: v01.07 (2026-11-20) — Copy Name 모드 리스트의 `Sort Base` / `Sort Targets` 버튼 이름을 `Sort` 로 통일. v01.06 = 콤보(Mode · Match)의 고른 값이 검게 보이지 않던 문제 수정. v01.05 = 설정 패널에서 위쪽 화면과 겹치는 항목 제거 (2.3). v01.04 = **Default / Copy Name 모드** · 공용 리스트 위젯. v01.03 = 에디터 스타일 · Load Selected 수정. v01.01 = 모달 창 → **도킹 탭**
- **엔진**: UE **5.4 이상** (EUW 에셋이 5.4 로 저장돼 있다)
- **메뉴**: `Tools > JUN > Asset > JUN Renamer...`
- **모듈**: `jun_tools/tools/A00530_jun_renamer/`
- **규칙 파일**: `Config/jun_asset_rename_rules.csv`
- **에셋**: `Content/A00530_jun_renamer/EUW_JUNRenamer.uasset` (`/JUNTools/A00530_jun_renamer/EUW_JUNRenamer`)

---

## 1. 출처

| 기능 | 가져온 곳 |
|------|-----------|
| 에셋 불러오기 · 필터 · Search/Replace(Anywhere / Prefix / Suffix) · Prefix · Suffix · 네이밍 규칙(CSV) · 텍스트 정리 · 미리보기 · 실행 | MANUProject `Tools > Asset Renamer` (`MANUEditor` 플러그인의 C++ Slate 탭 `SMANUAssetRenamerWidget`) |
| **Trim Front / Trim Rear** + `-1 Front` / `-1 Rear` 버튼 | 마야 `A00330_NamingTool` > Quick Rename > Selection 의 `-1 Front` / `-1 Rear` |
| **Copy Name** (Base → Targets, Prefix · Suffix · Search · Replace) | 마야 `A00330_NamingTool` > Copy Name |

원본은 C++ 위젯이지만 JUN_UE 는 C++ 모듈이 없는 플러그인이다. 그래서 화면은 파이썬 uclass 를
**디테일 패널**로 그린 것이고, 실행은 그 안의 **버튼**(`CallInEditor`)이다.
v01.01 부터 이 디테일 패널을 **Editor Utility Widget 탭** 안에 띄운다 — 아래 2.1.

---

## 2. 화면

```
┌ JUN Renamer (탭) ──────────────────────────────────────────────────┐
│ ▼ Assets                                                           │
│   Loaded            12 asset(s) | 12 shown | 3 will be renamed      │
│   Use Path Filter   [ ]     Path Filter [            ]              │
│   Name Filter       [            ]                                  │
│   [Load Selected] [Load Folder] [Load All /Game] [Clear]            │
│ ▼ Rename                                                           │
│   Search [   ]  Replace [   ]  Match [Anywhere v]  Case Sensitive [ ]│
│   Prefix [   ]  Suffix  [   ]                                       │
│   Trim Front [0]   Trim Rear [0]                                    │
│   Use Naming Convention [ ]  Remove Spaces [ ]                      │
│   Collapse Double Underscores [ ]  Capitalize Words [ ]             │
│   Rename Preview   ▶ 12 elements                                    │
│   [-1 Front] [-1 Rear] [Reset Trim] [Preview] [Rename]              │
│ ▼ Copy Name                                                        │
│   Base     ▶ 2 elements      Targets ▶ 2 elements                   │
│   Prefix [   ]  Suffix [   ]  Search [   ]  Replace [   ]           │
│   Case Sensitive [x]   Copy Preview ▶ 2 elements                    │
│   [Base <- Selection] [Targets <- Selection] [Sort Base]            │
│   [Sort Targets] [Preview Copy] [Copy Name]                         │
└────────────────────────────────────────────────────────────────────┘
```

(실제 배치는 디테일 뷰가 정한다 - 위는 구성만 보인 것)

- **미리보기 한 줄**: `Ready      SM_Rock  ->  SM_Rock_01    (StaticMesh, /Game/Env)`
- 이름 변경은 `Rename` / `Copy Name` 버튼으로만 한다.
- **탭을 닫아도 입력값과 목록은 남는다**(에디터를 끄면 사라진다). 메뉴를 다시 누르면 같은 값으로 열린다.

### 2.1 탭으로 열린다 (v01.01)

- 레벨 에디터의 **도킹 탭**이라 모달이 아니다 — **탭을 띄운 채 콘텐츠 브라우저를 클릭 · 선택**할 수 있다.
  다른 탭처럼 끌어서 붙이거나 떼어 쓸 수 있다.
- 메뉴를 다시 누르면 새 탭을 만들지 않고 **열린 탭을 앞으로** 가져온다.
- 구조: EUW `EUW_JUNRenamer` 의 루트 위젯 `DetailsView` 에 설정 오브젝트를 `set_object()` 로 꽂는다.
  탭 제목은 EUW 의 Class Defaults > `Tab Display Name`(= `JUN Renamer`).
- **미리보기가 저절로 바뀐다** — 칸 편집이 끝나면(Enter · 포커스 이동 · 체크 · 드롭다운) 다시 계산한다.
  `Preview` / `Preview Copy` 버튼은 칸 밖의 변화(다른 곳에서 에셋 이름이 바뀜 등)를 반영할 때 쓴다.
- **EUW 를 못 찾거나 탭을 못 띄우면** v01.00 의 모달 창으로 대신 연다(Output Log 에 경고).
  모달 창에서는 미리보기가 버튼으로만 갱신되고, 떠 있는 동안 콘텐츠 브라우저를 누를 수 없다.

### 2.2 원본 모양 UI — 스파이크 (v01.02, 화면 확인 대기)

원본 Asset Renamer 처럼 보이게 바꾸는 중이다. EUW 루트를 `VerticalBox`(`Root`) 하나로 바꾸고,
**화면은 파이썬(`ui_tab.py`)이 실행 중에 조립**한다(`unreal.new_object()` + `add_child()`).
에셋과 코드의 약속은 `Root` 하나뿐이라 화면을 고칠 때 에셋을 건드리지 않는다.

지금 탭의 구성 (위 → 아래):

```
Name Filter: [Search asset names (e.g. SK_, MT_, Character)...]  4/4 matched  [Load Selected]
Search: [Text to find]  Replace: [Text to replace]  [Anywhere v]
4 assets loaded, 2 will be renamed
Type        Current Name        ->   New Name        Status
Material    XRock_A             ->   Rock_A          Ready          ← 행을 누르면 콘텐츠 브라우저에서 그 에셋을 찾는다
...
─ 기존 설정 패널 (DetailsView, 역시 파이썬으로 생성) - 툴 전체 기능 ─
```

- 위쪽 입력칸과 아래 설정 패널은 **같은 설정 오브젝트**를 쓴다. 한쪽을 고치면 다른 쪽도 맞춰진다.
- `Name Filter` 는 원본처럼 2 글자부터 거른다(비우면 전부). Search / Replace 는 Enter · 포커스 이동 때 반영.
- 목록 색은 원본과 같다 — 타입 열 연보라, Ready 행의 새 이름 초록, 바뀌지 않는 행 회색.
- 스파이크의 목적은 **파이썬이 만든 위젯이 탭에 실제로 그려지는지** 확인하는 것이다(헤드리스로는 볼 수 없다).
  확인되면 나머지(경로 필터 · 접두/접미 · 체크박스 · 아래쪽 버튼 · Trim · Copy Name)를 같은 방식으로 옮기고
  설정 패널을 걷어낸다 — 그 전에 계획서를 쓴다.
- UI 문자열은 전부 영어다(원본은 한국어였다).
- **v01.03** — 위젯을 에디터 스타일 판(`EditorUtilityButton` · `EditorUtilityEditableTextBox` ·
  `EditorUtilityComboBoxString` · `EditorUtilityScrollBox`)으로 바꾸고 글자는 에디터 기본 글꼴(9)을 입혔다.
  v01.02 는 게임용 기본 스타일이라 글자가 24 로 컸다. 필터 · 옵션 줄은 원본처럼 어두운 박스에 담았고,
  목록 행은 투명 버튼(마우스를 올리면 살짝 밝아짐)이다.
- **v01.03** — 위쪽 `Load Selected` 가 에디터에서 동작하지 않던 문제를 고쳤다. 원인은 아래 "함정".

> **함정 — 파이썬 콜백이 GC 뒤 끊긴다.** `add_callable` 이 만드는 중계 오브젝트는 **파이썬이 참조를 쥔 위젯의
> 델리게이트를 통해서만** GC 에서 지켜진다(`FPyReferenceCollector`). v01.02 는 그 버튼을 지역 변수로 만들고 버려서,
> 에디터의 주기 GC(약 60 초) 뒤 연결이 소리 없이 끊겼다 — 먼저 친 `Search` 는 먹고 뒤에 친 `Replace` 가 안 먹은 것도 같은 이유.
> 이제 콜백을 단 위젯은 모두 세션 동안 붙잡는다(`ui_tab.connect()`). 헤드리스 `obj gc` 로 재현 · 확인했다.

> ⚠️ **EUW 는 UE 5.4 에디터에서만 고치고 저장할 것.** 5.5 이상에서 저장하면 그 버전으로 다시 저장되어
> 5.4 에서 열 수 없다. (코드는 실패하면 모달 창으로 대체되지만 탭은 쓸 수 없게 된다.)

---

### 2.3 모드 — Default / Copy Name (v01.04)

탭 맨 위 `Mode:` 콤보로 고른다. 고른 모드는 세션 동안 남는다.

| 모드 | 화면 |
|------|------|
| **Default** | 2.2 의 원본 모양 화면 + 설정 패널(**Assets · Rename 섹션만** — 접히는 Copy Name 섹션은 없앴다) |
| **Copy Name** | Base / Targets **리스트 두 개** + 이름 칸 + 미리보기 + `Copy Name` 버튼 (3.3) |

```
Mode: [Copy Name v]
┌───────────────────────────────────────────────────────────┐
│ Base              Number: 2  │ Targets           Number: 2 │
│ ┌──────────────────────────┐ │ ┌─────────────────────────┐ │
│ │ SK_Hero                  │ │ │ ABP_Temp                │ │
│ └──────────────────────────┘ │ └─────────────────────────┘ │
│ [     Load Selected      ]   │ [     Load Selected     ]   │
│ [Add][Del][Up][Down][Sort]   │ [Add][Del][Up][Down][Sort]  │
└───────────────────────────────────────────────────────────┘
Prefix [   ]  Suffix [   ]
Search [   ]  Replace [   ]  [x] Case Sensitive
2 pair(s), 2 will be renamed
Base     Target     ->  New Name      Status
                                         [ Copy Name ]
```

- 리스트는 공용 위젯 **`AssetList`**(`jun_tools/widgets/asset_list.py`)다 — 마야 `JUN_mod_tsl_qt_v01` 의 대응.
  **"TSL" 은 마야 `textScrollList` 의 이름이라 언리얼 용어가 아니다.** UMG 의 같은 역할은 `ListView` 인데 행 위젯
  에셋이 하나 더 필요해서, 이 위젯은 `ScrollBox` 에 행을 쌓는다. 사용법은 [../Widgets/AssetList.md](../Widgets/AssetList.md).
- 모달 대체 창(EUW 를 못 띄울 때)에는 예전처럼 설정 패널에 Copy Name 섹션이 남아 있다.

**Default 모드 설정 패널** (v01.05) — 위쪽 화면과 겹치는 항목은 뺐다.

| 섹션 | 남은 것 | 위쪽 화면으로 옮긴 것 (패널에서 제거) |
|------|---------|----------------------------------------|
| Assets | Use Path Filter · Path Filter · `Load Folder` · `Load All /Game` · `Clear` | Loaded(→ 상태 줄 · `n/m matched`) · Name Filter · `Load Selected` |
| Rename | Case Sensitive · Prefix · Suffix · Trim Front · Trim Rear · Use Naming Convention · Remove Spaces · Collapse Double Underscores · Capitalize Words · `-1 Front` · `-1 Rear` · `Reset Trim` · `Rename` | Search · Replace · Match · Rename Preview(→ 목록) · `Preview`(→ 자동 갱신) |

- 뺀 항목은 지운 게 아니라 **`Filter and Preview` 섹션**으로 옮겼다 — 탭의 패널은 Assets · Rename 만 보여서 숨고,
  EUW 를 못 띄울 때의 모달 창(위쪽 화면이 없다)에서만 보인다.
- 설정 클래스 구성이 바뀌어서 **에디터를 재시작해야** 보인다. 재시작 없이 리로드만 하면 Output Log 에
  `the settings panel layout changed in this version. Restart the editor to see it.` 가 한 번 뜬다.

## 3. 쓰는 법

### 3.1 Rename (원본 Asset Renamer)

1. 콘텐츠 브라우저에서 에셋(또는 폴더)을 고르고 `Tools > JUN > Asset > JUN Renamer...`.
   목록이 비어 있고 선택한 에셋이 있으면 **열면서 바로 불러온다**(이미 불러온 목록은 덮지 않는다).
   탭을 띄운 채 다른 에셋을 고르고 **`Load Selected`** 를 눌러도 된다.
   - `Load Folder` — 선택한 폴더 아래 전부(하위 폴더 포함)
   - `Load All /Game` — 프로젝트 전체. 1000 개가 넘으면 한 번 묻는다
   - 리디렉터와 레벨(World)은 원본처럼 뺀다(폴더 · 전체 불러오기)
2. 입력칸을 채우면 `Rename Preview` 배열에 결과가 나온다(칸 편집이 끝날 때 자동 · `Preview` 버튼으로도).
3. **`Rename`** → 확인 창 → Ready 행만 이름을 바꾸고 저장한다.

**새 이름 계산 순서**

```
Trim Front/Rear → Search/Replace → Prefix → Suffix → (수동 입력이 하나도 없을 때만) Naming Convention → 텍스트 정리
```

| 입력 | 동작 |
|------|------|
| `Search` / `Replace` + `Match` | `Anywhere` = 전부 바꿈 · `Prefix Only` / `Suffix Only` = 이름 앞 / 끝에 있을 때만. 글자 그대로(정규식 아님) |
| `Case Sensitive` | Search · Prefix · Suffix 비교. **기본 꺼짐** (원본 FString 기본값이 대소문자 무시) |
| `Prefix` / `Suffix` | **이미 있으면 다시 붙이지 않는다** (원본과 같다). `sm_Rock` 에 `SM_` → 그대로 |
| `Trim Front` / `Trim Rear` | **새 기능.** 지금 이름의 앞 / 뒤에서 지울 글자 수 |
| `Use Naming Convention` | 타입별 규칙(CSV) — 아래 6장. **기본 꺼짐** |
| `Remove Spaces` · `Collapse Double Underscores` · `Capitalize Words` | 마지막에 적용 |

### 3.2 앞글자 / 뒷글자 한 글자씩 지우기 (A00330 Quick Rename)

- **`-1 Front`** 를 누를 때마다 `Trim Front` 가 1 오르고 미리보기가 바로 갱신된다. `-1 Rear` 도 같다.
  원하는 만큼 눌러서 미리보기를 보고 → **`Rename`**.
- 숫자를 직접 적어도 된다(`Trim Front = 3`). `Reset Trim` 은 둘 다 0 으로.
- **`Rename` 이 끝나면 Trim 은 0 으로 돌아간다** — 그대로 두면 다음 `Rename` 이 또 지운다.

> **마야와 다른 점** — 마야의 `-1 Front` 는 누르는 즉시 씬 오브젝트 이름을 바꿨다. 에셋 이름 변경은
> 디스크 저장 · 참조 수정까지 따라오는 무거운 작업이라 **한 번 누를 때마다 바로 바꾸지 않고
> 미리보기에 쌓은 뒤 `Rename` 한 번으로** 실행한다. 글자 수만큼 저장이 반복되지 않는다.

### 3.3 Copy Name (A00330 Copy Name)

`Targets[i]` 의 이름을 `Prefix + (Search/Replace 한) Base[i] 이름 + Suffix` 로 바꾼다. 순서 기준.

1. `Mode:` 를 **Copy Name** 으로.
2. 콘텐츠 브라우저에서 **Base** 에셋을 고르고 Base 리스트의 **`Load Selected`**. Targets 도 같은 방식.
   - `Add` = 중복 없이 뒤에 붙임 · `Del` / `Up` / `Down` = 고른 행(누르면 파랗게) 삭제 · 이동.
   - 순서가 원하는 대로가 아니면 각 리스트 아래 **`Sort`**(이름순).
   - 행을 누르면 콘텐츠 브라우저가 그 에셋으로 옮겨 간다. 지워진 에셋은 빨간 `(None)`.
3. `Prefix` / `Suffix` / `Search` / `Replace` 는 Enter(또는 포커스 이동), `Case Sensitive` 는 체크하면 미리보기가 바뀐다.
4. **`Copy Name`** → 확인 창 → 실행. 바꿀 행(Ready)이 없으면 버튼이 꺼진다. 실행 뒤 리스트에 새 이름이 보인다.

| 입력 | 동작 |
|------|------|
| `Search` / `Replace` | **Base 이름 안에서만** 바꾼다. Prefix / Suffix 안의 글자는 바뀌지 않는다. 예: Base `SK_Hero_01`, Search `_01`, Replace 빈칸, Prefix `ABP_` → `ABP_SK_Hero` |
| `Case Sensitive` | Search 비교. **기본 켜짐** (마야 Copy Name 과 같다) |
| `Prefix` / `Suffix` | **항상** 붙인다 (마야와 같다. Rename 섹션처럼 "없을 때만" 이 아니다) |
| 개수 불일치 | 짧은 쪽 개수만큼만. `Copy Preview` 첫 줄에 `[WARN]` |
| 결과가 빈 이름 | Base 이름 전체를 지운 경우 — `empty name` 으로 건너뛴다 |

> **`Set suffix` 대신 `Suffix`** — 마야의 `Set suffix` 는 *대상이 세트일 때만* 붙었다. 세트는 DG 노드라
> 같은 이름을 못 쓰기 때문이다. 언리얼에는 세트가 없고, 같은 이름을 못 쓰는 경우는
> **같은 폴더**일 때다(Base 와 Target 이 한 폴더에 있으면 Base 이름 그대로는 `Name taken`).
> 그래서 조건 없이 모든 대상에 붙는 `Suffix` 로 두었다. 기본값은 빈칸이다.

---

## 4. 미리보기 상태

| 상태 | 뜻 | 실행 시 |
|------|----|---------|
| `Ready` | 바뀐다 | 이름 변경 |
| `No change` | 새 이름이 지금 이름과 같다 | 건너뜀 |
| `Name taken` | 같은 폴더에 그 이름이 이미 있다 / 이번 묶음에서 다른 행이 먼저 그 이름을 가져갔다. 단 **이번에 다른 이름으로 비켜 줄 에셋**의 이름은 받아도 된다 | 건너뜀 |
| `empty name` | 다 지워졌다 (Trim 이 이름보다 길다 등) | 건너뜀 |
| `invalid character: ...` | 에셋 이름에 못 쓰는 글자(공백 `. , / : | & ! ~ @ # ( ) { } [ ] = ; ^ % $ ' "` 등) | 건너뜀 |
| `Missing` | 실행 순간 에셋을 찾을 수 없다 | 건너뜀 |

- 언리얼 패키지 이름은 대소문자를 가리지 않으므로 충돌 판정도 대소문자를 무시한다.
- 미리보기는 최대 **500 행**(원본과 같다). Path / Name 필터를 쓰면 제한 없이 전부.
- `Name Filter` 는 이름 · 타입 · 경로 어디에든 들어 있으면 남긴다. `Path Filter` 는 경로 앞부분 일치.
  둘 다 대소문자 무시 (원본 `Contains` / `StartsWith` 기본값과 같다).

---

## 5. 실행 시 일어나는 일

- Ready 행을 `AssetTools.rename_assets()` **한 번**에 넘긴다 (원본과 같다).
- 엔진이 참조하는 에셋을 불러와 경로를 고치고 저장한다. 실측(헤드리스, 2026-11-20): 머티리얼
  인스턴스의 부모 머티리얼 이름을 바꾸면 인스턴스가 새 이름을 가리키고, 더티 패키지 0 개,
  옛 자리 리디렉터 없음. 고칠 수 없는 참조가 있을 때만 리디렉터가 남는다 → 폴더 우클릭 > `Fix Up Redirectors`.
- 바꾼 에셋(과 남은 리디렉터)만 저장한다. 원본은 에디터의 더티 패키지를 **전부** 저장했는데
  (`SaveDirtyPackages`), 이름 변경과 무관한 작업까지 저장되는 일을 막았다.
- 결과는 Output Log(`[JUNTools] Renamer:`)와 알림 창에 나온다.
- **되돌리기(Ctrl+Z)는 기대하지 말 것** — 에셋 이름 변경은 원래 언두 대상이 아니다. 같은 툴로 다시 바꾼다.

---

## 6. 네이밍 규칙 (`Use Naming Convention`)

`Config/jun_asset_rename_rules.csv` — 원본 `MANUEditor/config/AssetRenameRules.csv` 를 그대로 복사했다.
수정하면 **다음 Preview 부터** 반영된다(파일 수정 시각을 보고 다시 읽는다).

```
AssetClass,NewPrefix,NewSuffix,PrefixesToRemove,SuffixAliasesToRemove,StringReplacements,SearchCase,Priority
UStaticMesh,SM_,,SM_|Mesh_|SK_,"",,IgnoreCase,100
```

- 에셋 클래스(조상 포함)가 `AssetClass` 와 맞는 규칙 중 **Priority 가 가장 높은 것** 하나를 쓴다.
  `PrefixesToRemove` 중 처음 맞는 것 하나를 떼고 `NewPrefix + 이름 + NewSuffix`.
- **수동 입력(Search · Prefix · Suffix · Trim)이 하나라도 있으면 규칙은 쓰지 않는다** (원본 규칙).

**원본 대비 달라진 점** — 원본은 에셋을 **로드**해서 `IsA` 로 판정했고, 코드의 클래스 표에 없는
클래스(`TextureCube` · `BehaviorTree` · `MediaTexture` · `LiveLinkFramePreProcessor` 등)의 규칙은 건너뛰었다.
여기서는 에셋 레지스트리의 클래스 · 조상 클래스 이름으로 판정한다 — **로드하지 않아 빠르고**,
CSV 에 적힌 클래스가 엔진에 있으면 그 규칙이 실제로 적용된다.

> ⚠️ **원본 규칙에서 그대로 옮겨 온 버릇** — 그래서 기본값을 꺼 두었다 (원본은 켜짐).
> - **우선순위가 같으면 CSV 에서 먼저 나온 규칙**이 이긴다. `WidgetBlueprint` 는 `Blueprint` 의 자식이라
>   `UBlueprint`(70) 가 먼저 걸려 **`WBP_` 가 아니라 `BP_`** 가 된다.
> - 텍스처 공통 정리 줄(`UTexture,,,T_|TX_...,100`)은 쉼표가 한 칸 많아 **Priority 가 0 으로 읽힌다**.
>   그 결과 접미사 없는 텍스처는 전부 첫 번째 텍스처 규칙을 받아 **`T_<이름>_DIF`** 가 된다
>   (`Rock_Normal` → `T_Rock_Normal_DIF`).
> - 이미 `_DIF` `_NOR` 등 텍스처 접미사로 끝나는 이름은 아예 건드리지 않는다.
>
> 원본과 같은 결과를 내도록 일부러 고치지 않았다. CSV 를 고치면(우선순위 · 순서) 바로 반영된다.

---

## 7. 제약 (파이썬 + 디테일 패널이라서)

| 제약 | 이유 | 대응 |
|------|------|------|
| ~~창이 떠 있는 동안 콘텐츠 브라우저를 클릭할 수 없다~~ | v01.00 의 모달 다이얼로그 탓 | **v01.01 에서 해결** — EUW 탭 (2.1). 모달 대체 창에서만 남는다 |
| 미리보기는 칸 편집이 **끝났을 때** 바뀐다 (글자마다가 아님) | 엔진이 `on_property_changed` 를 편집 완료 시점에 보낸다 | **`Rename` / `Copy Name` 은 실행 직전에 반드시 다시 계산** — 오래된 미리보기로 바뀌는 일은 없다 |
| 프로퍼티 · 버튼 **구성**을 바꾸면 에디터 재시작 | 탭이 붙잡은 오브젝트 때문에 클래스를 세션당 한 번만 등록한다 (다시 등록하면 엔진 ensure) | 코드 수정은 DEV_MODE / `Reload JUN Tools` 로 그대로 반영된다 |
| EUW 를 5.5+ 에서 저장하면 5.4 에서 못 연다 | 언리얼 에셋은 하위 호환만 된다 | EUW 는 5.4 에서만 고친다 (2.1) |
| 미리보기 배열을 고칠 수 있게 보인다 | 파이썬 uproperty 에 `EditConst` 플래그를 줄 수 없다 | 표시 전용 — 고쳐도 아무 일도 없고 다음 Preview 가 덮어쓴다 |
| 원본의 미리보기 표(색 · 더블클릭으로 위치 찾기) | Slate 리스트 뷰는 C++ 전용 | 상태 글자 + 경로를 한 줄에 |

원본에 있던 CSV 내보내기 / 가져오기(가져오기는 미구현)는 옮기지 않았다.

---

## 8. 검증

`Docs/verify/verify_a00530_renamer.py` — 스크래치 프로젝트에서 헤드리스로 돌린다.

```
UnrealEditor-Cmd.exe <Scratch>.uproject -PLUGIN="<JUN_UE>/JUNTools.uplugin" ^
    -run=pythonscript -script="<JUN_UE>/Docs/verify/verify_a00530_renamer.py" ^
    -unattended -nosplash -nullrhi -AbsLog="verify_a00530.log"
```

`/Game/JUNRenamerTest` 에 머티리얼 · 머티리얼 인스턴스를 만들어 실제로 이름을 바꾸고 디스크까지 확인한 뒤 지운다.
v01.01: EUW 구조(루트 `DetailsView` · 변수 노출 · 탭 제목), `set_object`, 칸 편집 이벤트 → 미리보기 갱신,
탭을 못 띄울 때 모달 대체, DEV_MODE · `Reload JUN Tools` 뒤에도 클래스 · 오브젝트 · 값이 유지되는지까지 본다.
UE 5.4.4 · 5.7.4 에서 **43/43** (2026-11-20).

**탭이 실제로 뜨는지 · 콘텐츠 브라우저를 누를 수 있는지 · 버튼이 보이는지는 헤드리스로 볼 수 없다** —
커맨드렛은 탭을 아예 등록하지 않는다. 에디터 체크리스트는 계획서 §6.2
([../Plans/A00530_JUNRenamer_EUW_Tab_Plan.md](../Plans/A00530_JUNRenamer_EUW_Tab_Plan.md)).
