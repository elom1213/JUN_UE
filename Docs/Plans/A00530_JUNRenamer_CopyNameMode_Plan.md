# A00530 — JUN Renamer · Copy Name 모드 + 공용 리스트 위젯 계획서

- **작성일**: 2026-11-20
- **대상**: `A00530_jun_renamer` (툴 v01.03 → v01.04, 플러그인 v01.07 → v01.08)
- **상태**: **구현 완료 (2026-11-20)** — 헤드리스 5.4 · 5.7 71/71. 에디터 눈 확인 대기

---

## 0. 요청

1. 모드를 **Default / Copy Name** 중에서 고른다.
2. Copy Name 모드에서는 **Base · Targets 리스트 두 개**가 보이고, Base 를 불러올 수 있다.
   `Copy Name` · `Sort Base` · `Sort Targets` 는 버튼으로.
3. 설정 패널의 접히는 **Copy Name 섹션은 없앤다**.
4. 리스트를 마야 `JUN_mod_tsl_qt_v01` 처럼 **공용 위젯**으로 만들어 앞으로의 툴이 같이 쓴다.

## 1. 용어 — TSL

TSL 은 마야 `textScrollList` 의 줄임말이라 **언리얼 용어가 아니다.** UMG 에서 같은 역할은 **`ListView`**
(항목마다 행 위젯을 만드는 목록)이다. 다만 `ListView` 는 행 위젯 블루프린트(`UserObjectListEntry` 구현)가
에셋으로 하나 더 필요해서, 이 위젯은 `ScrollBox` 에 행을 직접 쌓는다. 그래서 코드 · 문서에서는
**"Asset List"(공용 리스트 위젯)** 라고 부른다. 마야 문서와 대응시킬 땐 "TSL 에 해당" 이라고 적는다.

## 2. 설계

### 2.1 공용 위젯 — `jun_tools/widgets/`

| 모듈 | 내용 |
|------|------|
| `widgets/umg.py` | 위젯 조립 헬퍼 — 에디터 글꼴 · `EditorUtility*` 위젯 생성 · 박스 슬롯(fill/pad) · 어두운 그룹 박스 · **`connect()`(콜백 + GC 보호)**. A00530 `ui_tab.py` 에 있던 것을 옮긴다 |
| `widgets/asset_list.py` | **`AssetList`** — 마야 `JUN_mod_tsl_qt_v01` 대응 |

`AssetList` (마야 대응):

```
Base                         Number: 2      ← 제목(bold) + 개수
┌──────────────────────────────┐
│ SK_Hero                      │   행을 누르면 선택(강조) + 콘텐츠 브라우저에서 그 에셋을 찾는다
│ SK_Villain                   │   지운 에셋은 (None) 빨간 글씨
└──────────────────────────────┘
[ Load Selected ]                           ← 마야 "Select Objects" (UE 에서 Select 는 다른 뜻이라 Load)
[Add][Del][Up][Down][Sort]                  ← show_* 로 켜고 끈다. Reverse · Clear 는 선택
```

- 옵션: `title` · `show_load` / `show_add` / `show_del` / `show_up` / `show_down` / `show_sort` / `show_reverse` / `show_clear` ·
  `load_label` · `sort_label` · `on_changed(items)`.
- 항목 = UObject(에셋). `items()` / `set_items()` / `append_unique()` / `selected_index`.
- 선택은 한 행(마야는 다중 선택 — 버튼 클릭으로는 Ctrl 을 읽을 수 없어 단일로 시작).
- DEV_MODE 리로드: `jun_tools.run()` 이 툴 패키지와 함께 `jun_tools.widgets` 도 비운다.

### 2.2 A00530 화면

```
Mode: [Default v]                              ← Default / Copy Name
┌ Default ───────────────────────────────┐   ┌ Copy Name ─────────────────────────────┐
│ (지금 화면 그대로)                      │   │ [Base list]        [Targets list]       │
│ 필터 · 옵션 · 목록                      │   │   Load Selected      Load Selected       │
│ 설정 패널 — Assets · Rename 만          │   │   Add Del Up Down    Add Del Up Down     │
│ (Copy Name 섹션 없음)                   │   │   Sort Base          Sort Targets        │
└────────────────────────────────────────┘   │ Prefix [ ] Suffix [ ]                    │
                                              │ Search [ ] Replace [ ] [x] Case Sensitive│
                                              │ 2 pair(s), 2 will be renamed             │
                                              │ Base | Target | -> | New Name | Status   │
                                              │ (미리보기)                               │
                                              │                          [ Copy Name ]   │
                                              └──────────────────────────────────────────┘
```

- 모드 전환 = UMG `WidgetSwitcher`. 고른 모드는 세션에 남는다.
- 설정 패널은 `DetailsView.categories_to_show = [Assets, Rename]` 으로 Copy Name 섹션을 숨긴다
  (클래스 구성은 그대로 → 에디터 재시작 불필요, 모달 대체 창에는 그대로 남는다).
- `Sort Base` / `Sort Targets` = 각 리스트의 Sort 버튼(`sort_label` 로 이름을 붙인다).
- 값의 정본은 여전히 설정 오브젝트(`base` · `targets` · `copy_*`). 리스트 · 입력칸 → 설정 → `preview_copy()` → 미리보기.

## 3. 검증

- 헤드리스(5.4 · 5.7): 공용 리스트(Load/Add/Del/Up/Down/Sort/Reverse, 선택, `on_changed`), 모드 전환,
  Copy Name 페이지 입력 → 설정 → 미리보기, Copy Name 실행, `obj gc` 뒤 콜백 생존, 기존 항목 전부.
- 에디터 눈 확인: 모드 콤보 · 두 리스트 배치 · 버튼 · 미리보기.

## 4. 범위 밖

- 리스트 다중 선택 · 드래그 정렬 · 콘텐츠 브라우저에서 끌어다 놓기
- Default 모드의 나머지 원본 UI 이식(경로 필터 · 접두/접미 · 체크박스 · 아래 버튼) — 다음 단계
