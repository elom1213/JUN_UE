# A00510 — Bone Display Settings

스켈레탈 메시 / 애니메이션 에디터 뷰포트에서 **본을 보이게 하는 설정**을 팝업 하나로 처리한다.

- **버전**: v01.01 (2026-09-01) — Apply 버튼 추가
- **메뉴**: `Tools > JUN > Animation`
  - `Bone Display Settings...` — 팝업
  - `Show All Bones` — 다이얼로그 없이 바로 All Hierarchy
- **모듈**: `jun_tools/tools/A00510_bone_viewport/`

---

## 왜 만들었나

원래는 이렇게 타고 들어가야 한다.

```
뷰포트 툴바 > 눈 아이콘(Show flags) > Bones > All Hierarchy   (라디오 버튼)
                                   > Bone Draw Size            (스핀 박스)
```

메시를 열 때마다 반복해야 해서 불편하다.

---

## 할 수 있는 것 / 없는 것

| 기능 | 이 툴 | 이유 |
|------|-------|------|
| Bone Draw Mode (All Hierarchy 등 6종) | ✅ | `UPersonaOptions.DefaultBoneDrawSelection` — 전역 설정 오브젝트에 있다 |
| Show Bone Colors | ✅ 즉시 반영 | 그릴 때마다 설정을 읽는다 |
| **Bone Draw Size** | ❌ **불가** | 아래 참고 |

### Bone Draw Size 가 안 되는 이유

`BoneDrawSize` 는 설정 오브젝트가 아니라 **뷰포트 객체의 평범한 C++ 멤버**다.

```cpp
// Engine/Source/Editor/Persona/Public/AnimationEditorViewportClient.h
class FAnimationViewportClient ...
{
    void  SetBoneDrawSize(const float InBoneDrawSize);   // UFUNCTION 아님
    float BoneDrawSize = 1.0f;                           // UPROPERTY 아님
};
```

`UPROPERTY` 도 `UFUNCTION` 도 아니고 config 에도 없다. **리플렉션이 존재하지 않으므로
파이썬에서 읽거나 쓸 방법이 아예 없다.** 에디터를 새로 열 때마다 1.0 으로 돌아가는 것도 같은 이유다.

> C++ 에디터 모듈을 만들면 가능하다. `IPersonaViewport::GetViewportClient()` 로 뷰포트 클라이언트를
> 얻어 `SetBoneDrawSize()` 를 부르면 된다(둘 다 Public 헤더). 다만 그 순간 이 플러그인은
> 컴파일이 필요해지고 엔진 빌드에 묶인다 — [설계 가이드 3장](../00_UE_Tool_Plugin_Guide.md) 참고.
> 그래서 지금은 C++ 없이 되는 범위까지만 만들었다.

---

## 동작

### `Show All Bones` (메뉴 한 번 = 끝)

`DefaultBoneDrawSelection` 을 `All Hierarchy(5)` 로 바꾼다. 눈 아이콘 → Bones → 라디오 버튼
3단계가 **클릭 한 번**이 된다. 일상적으로는 이쪽을 쓰게 된다.

### `Bone Display Settings...` (팝업)

현재 값이 채워진 팝업이 뜬다.

| 항목 | 위젯 | 내용 |
|------|------|------|
| Bone Draw Mode | 드롭다운 | None / Selected Only / Selected and Parents / Selected and Children / Selected and Parents and Children / **All Hierarchy** |
| Show Bone Colors | 체크박스 | 본을 여러 색으로 |
| **Apply** | 버튼 | 지금 값을 적용한다. **창은 그대로 떠 있다** |
| **Reset** | 버튼 | 창을 열었을 때의 값으로 되돌려 적용한다 |

**Apply 가 주 경로다.** 눌러도 창이 닫히지 않으므로, 창을 띄워 둔 채 모드를 바꿔 가며
뷰포트를 확인할 수 있다. 잘못 적용했으면 **Reset** 이 창을 열었을 때의 값으로 되돌린다.

창 아래 버튼은 이렇게 동작한다.

| 버튼 | 하는 일 |
|------|---------|
| OK | 아직 적용 안 된 값이 남아 있으면 적용하고 닫는다 (Apply 를 이미 눌렀으면 아무것도 안 바뀐다) |
| Cancel | 그냥 닫는다. **이미 Apply 한 것은 되돌리지 않는다** — 그건 Reset 의 몫이다 |

무엇이 어떻게 바뀌었는지는 매번 Output Log 에 남는다.

```
[JUNTools] Bone display: Bone Draw Mode : Selected Only -> All Hierarchy
[JUNTools] Applies to skeletal mesh editors opened from now on. For an editor that is
           already open, click any bone in the Skeleton Tree to refresh.
```

---

## ⚠️ 두 가지 반영 시점

### 1. 이미 열려 있는 뷰포트는 바로 안 바뀐다

뷰포트는 **그릴 본 목록을 캐시**해 두고(`BonesToDraw`), 그 캐시는
`UpdateBonesToDraw()` 가 도는 순간에만 다시 계산된다.

- 에디터를 열 때
- 프리뷰 메시가 바뀔 때
- **본 선택이 바뀔 때**

파이썬은 설정 값만 바꿀 수 있고 이 함수를 부를 수 없다. 그래서:

> **이미 열려 있는 에디터라면 Skeleton Tree 에서 본을 아무거나 한 번 클릭하면 즉시 반영된다.**
> 새로 여는 에디터는 그냥 적용된 상태로 열린다.

`Show Bone Colors` 는 캐시를 안 타므로 바로 반영된다.

### 2. 값은 이번 세션 동안만 유지된다

엔진의 진짜 setter 는 값을 바꾼 뒤 `SaveConfig()` 로 ini 에 기록한다.

```cpp
void UPersonaOptions::SetDefaultBoneDrawSelection(uint32 In)
{
    DefaultBoneDrawSelection = In;
    SaveConfig();          // <- 파이썬에서 부를 수 없다
}
```

파이썬에는 `SaveConfig()` 가 노출돼 있지 않아 메모리상의 값만 바뀐다.
에디터를 껐다 켜면 원래대로 돌아온다.

- 실용적으로는 문제되지 않는다. 에디터를 켠 뒤 `Show All Bones` 를 **한 번** 누르면 그 세션 내내 유지된다
- 영구히 남기고 싶으면, 툴로 바꾼 뒤 뷰포트 메뉴에서 Persona 옵션을 아무거나 한 번 건드리면 된다
  (그때 엔진이 이 오브젝트의 config 프로퍼티를 통째로 저장하므로 우리 값도 함께 기록된다)

---

## 구조

```
A00510_bone_viewport/
├─ core.py    # UPersonaOptions CDO 읽기/쓰기 (UI 무의존)
└─ ui.py      # uenum + uclass 로 만든 디테일 뷰 팝업 + CallInEditor 버튼
```

UI 없이 그냥 부를 수도 있다.

```python
from jun_tools.tools.A00510_bone_viewport import core
core.set_bone_draw_mode(core.BoneDrawMode.ALL_HIERARCHY)
```

### 창을 닫지 않고 적용하는 법 — `CallInEditor` 버튼

파이썬만으로는 **모덜리스(non-modal) 창을 띄울 수 없다.** 창을 만드는 수단이
`show_object_details_view()` 하나뿐인데 그건 모달이라, v01.00 에서는 OK 로 창을 닫아야만
설정이 적용됐다. 값을 조금씩 바꿔 보려면 매번 메뉴를 다시 눌러야 했다.

해결은 창 자체가 아니라 **창 안**이다. 디테일 뷰는 인자가 없고 `CallInEditor` 메타가 붙은
UFUNCTION 을 **자동으로 버튼으로 그려 준다.**

```python
@unreal.ufunction(meta=dict(CallInEditor="true", Category="Bone Display", DisplayName="Apply"))
def apply(self):
    apply_settings(self)
```

엔진 쪽 판정은 딱 두 조건이다 (UE 5.7 실제 코드).

```cpp
// PropertyEditor/Private/PropertyCustomizationHelpers.cpp : CanCallFunctionBasedOnParams()
const bool bCanCall = TestFunction->GetBoolMetaData(NAME_CallInEditor) && (TestFunction->ParmsSize == 0);
```

그리고 `DetailCustomizations` 가 `RegisterCustomClassLayout("Object", FObjectDetails::MakeInstance)`
로 등록돼 있어서 **모든 디테일 뷰**가 이 버튼을 얻는다 — 우리 팝업도 포함이다.
파이썬 `@unreal.ufunction(meta=...)` 의 메타는 `FPyUFunctionDef::ApplyMetaData()` 가
`UFunction::SetMetaData()` 로 그대로 넘겨 주므로 C++ 로 쓴 것과 차이가 없다.

> 다른 툴에도 그대로 쓸 수 있는 패턴이다. **모달 다이얼로그 안에 "닫지 않는 동작"을 넣고 싶으면
> 프로퍼티가 아니라 인자 없는 UFUNCTION 을 추가한다.**

### 코드에서 눈여겨볼 점

- `unreal.PersonaOptions` 는 **존재하지 않는다.** 이 클래스는 파이썬용으로 생성되지 않으므로
  CDO 를 경로로 직접 찾는다: `unreal.find_object(None, "/Script/UnrealEd.Default__PersonaOptions")`
- 그렇게 얻은 오브젝트는 프로퍼티 이름이 파이썬 관례(snake_case)가 아니라 **C++ 이름 그대로**다.
  `DefaultBoneDrawSelection` (O) / `default_bone_draw_selection` (X)
- 팝업은 `unreal.EditorDialog.show_object_details_view()`. 파이썬 `@unreal.uenum()` 은 드롭다운으로,
  `bool` uproperty 는 체크박스로 그려진다 — **C++ 없이 위젯을 만드는 방법**이므로 다른 툴에도 쓸 수 있다
- `@unreal.uclass()` 는 타입 등록이라 한 번만 만들고 재사용한다(`_types()`).
  DEV_MODE 리로드로 모듈이 다시 임포트돼 재등록돼도 문제없는 것은 확인했다

---

## 검증 기록

### v01.01 — Apply 버튼 (2026-09-01)

`UE_5.7` 헤드리스 + 스크래치 프로젝트 — **16/16 통과**
(`Docs/verify/verify_a00510_apply.py`, `UE_ADDITIONAL_PLUGIN_PATHS` 로 마운트).

- `apply` / `reset` 이 생성된 UClass 에 **진짜 UFunction 으로 등록**된다 (`unreal.find_object` 로 확인)
- 둘 다 인자를 받지 않는다 = `ParmsSize == 0` (엔진이 버튼을 그리는 조건)
- Apply 는 다이얼로그가 보여 주는 값을 그대로 쓰고, 두 번 눌러도 안전하다 (두 번째는 `nothing changed`)
- Reset 은 창을 열었을 때의 값으로 되돌리고, 기억해 둔 값이 없으면 경고만 남기고 아무것도 안 한다
- `show()` 를 빠져나갈 때 `_ALIVE` / `_ORIGINALS` 에 아무것도 안 남는다
- DEV_MODE 리로드 3회에도 uclass/uenum 재등록 문제 없음

> **버튼이 실제로 그려지는지는 헤드리스로 확인할 수 없다.** `-unattended` 면
> `ShowObjectsDetailsView()` 가 창을 만들지 않고 바로 false 를 돌려주므로 디테일 패널 자체가
> 안 만들어진다. 대신 엔진이 버튼을 그리는 **조건 두 개를 코드에서 읽어** 확인했고
> (위 "창을 닫지 않고 적용하는 법"), 그 조건을 헤드리스로 검사했다.
> 에디터에서 눈으로 볼 것 — `Bone Display` 카테고리 아래 `Apply` / `Reset` 버튼 두 개.

### v01.00 (2026-08-14)

`MANU_Engine_Prebuilt` 5.7.4 헤드리스 — **19/19 통과**.

- 모드 읽기/쓰기 왕복, `apply()` 변경 목록, quick 액션
- 다이얼로그 경로 3회 연속 실행 → DEV_MODE 리로드로 uclass/uenum 이 재등록돼도 에러 없음
- `-unattended` 에서는 다이얼로그가 즉시 false 를 반환해 cancel 분기를 탄다
