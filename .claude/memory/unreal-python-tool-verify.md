---
name: unreal-python-tool-verify
description: UE 파이썬 API 는 헤드리스 커맨드렛으로 확인한다 + 플러그인 Content/Python 자동 실행/자동 마운트
metadata: 
  node_type: memory
  type: reference
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-09-01T06:40:00.000Z
---

언리얼 파이썬 툴 작업 시 검증 방법과, 실측으로 확인된 동작들 (2026-08-14, `MANU_Engine_Prebuilt` 5.7.4).

**헤드리스 검증** ([[mayapy-headless-verify]] 의 언리얼 판):
```
UnrealEditor-Cmd.exe <Project>.uproject -run=pythonscript -script="<verify.py>" \
    -unattended -nosplash -nullrhi -AbsLog="<log>"
```
- 빈 `.uproject`(Modules 없음) + `Content/` + `Plugins/` 만 있으면 스크래치 프로젝트로 충분하다 → 사내 프로젝트를 건드리지 않고 검증 가능
- 결과는 로그의 `LogPython` 카테고리에서 grep

**확인된 동작**
- 활성화된 플러그인의 `Content/Python` 이 `sys.path` 에 올라가고 그 안의 `init_unreal.py` 가 자동 실행된다
- `.uplugin` 에 `"EnabledByDefault": true` 를 넣으면 **`.uproject` 에 등록하지 않아도** 자동 마운트된다 (`LogPluginManager: Mounting Project plugin ...`)
- `unreal.EditorDialog` = `UEditorDialogLibrary` (**EditorScriptingUtilities 플러그인**). `show_message(title, msg, AppMsgType.OK_CANCEL, AppReturnType.CANCEL)` → `AppReturnType`
- `-unattended` 면 다이얼로그가 **4번째 인자(기본값)를 즉시 반환**해서 헤드리스가 멈추지 않는다
- `unreal.ToolMenus.get()` 은 커맨드렛에서도 살아 있어 메뉴 등록 코드까지 검증된다
- **`UE_ADDITIONAL_PLUGIN_PATHS` 환경변수**(Windows 구분자 `;`, 에디터 전용)에 플러그인 **상위 폴더**를 넣으면
  프로젝트 `Plugins/` 가 비어 있어도 로드된다 → `Mounting External plugin <이름>`.
  프로젝트 파일을 안 건드리므로 **툴 배포는 복사 말고 이 방식**. 시작 시 1회만 읽음(재시작 필요).
  커맨드라인 `-PLUGIN=<경로>` 도 동일. 같은 이름 플러그인이 두 곳에 있으면 엔진이 하나만 채택한다

**C++ 없이 입력 위젯 만드는 법** (Editor Utility Widget 없이):
`@unreal.uenum()`+`unreal.uvalue()` → 드롭다운, `unreal.uproperty(bool)` → 체크박스로 놓고
`unreal.EditorDialog.show_object_details_view(title, obj, options)` 로 띄운다. 실측 확인됨.
모달이고 **디테일 뷰라 실시간 반영은 불가**(PostEditChangeProperty 를 파이썬에서 못 잡는다).

**창을 닫지 않고 동작을 실행하는 법 (2026-09-01 확인, UE 5.7)**: 파이썬으로 모덜리스 창은 못 만든다
(`ShowObjectsDetailsView` 가 `GEditor->EditorAddModalWindow()` 를 부른다). 대신 **창 안에 버튼**을 넣는다 —
인자 없는 UFUNCTION 에 `CallInEditor` 메타를 달면 디테일 뷰가 자동으로 버튼으로 그린다.
```python
@unreal.ufunction(meta=dict(CallInEditor="true", Category="X", DisplayName="Apply"))
def apply(self): ...
```
엔진 판정은 `CanCallFunctionBasedOnParams()` 의 `GetBoolMetaData("CallInEditor") && ParmsSize == 0` 둘뿐이고,
`DetailCustomizations` 가 `RegisterCustomClassLayout("Object", FObjectDetails::MakeInstance)` 라 **모든 디테일 뷰**에 붙는다.
파이썬 메타는 `FPyUFunctionDef::ApplyMetaData()` → `UFunction::SetMetaData()` 로 그대로 전달된다.
**헤드리스로는 버튼이 그려지는지 볼 수 없다** (`-unattended` 면 창 자체를 안 만든다) → 조건만 검사하고 눈으로 확인.
`@unreal.uclass()` 를 거치면 메서드가 네이티브로 치환돼 `inspect.signature` 가 실패한다(등록됐다는 증거).
`@unreal.uclass()` 는 모듈이 리로드돼 재등록돼도 문제없다(3회 연속 확인) — **단, 그 클래스의 이전 인스턴스가
아직 살아 있으면 아니다** (2026-11-20, A00530). 엔진이 재인스턴싱하며 PythonScriptPlugin ensure
`PySelf->ob_type == PyType` (PyWrapperObject.cpp:2031, `..._REINST_1`) 가 뜬다. 대책: 생성한 타입을
툴 패키지 밖(`jun_tools.tools.__dict__`)에 캐시해 **세션당 1회만 등록**하고, 메서드 몸체는
`importlib.import_module(__name__).func(self)` 로 최신 모듈에 디스패치 → DEV_MODE 리로드 코드도 그대로 반영.
오브젝트는 GC 되지 않게 참조를 붙잡을 것.

**모덜리스 창 = EUW + DetailsView (2026-11-20, A00530)**: 파이썬으로 위젯 트리는 못 만든다(`WidgetTree` protected) →
사람이 EUW 에 루트 `DetailsView` 하나를 넣어 두면, `EditorUtilitySubsystem.spawn_and_register_tab(bp)` → 위젯의
`DetailsView` 변수 → `set_object(파이썬 uclass 인스턴스)`. `on_property_changed` 는 `add_callable` 로 받는다.
탭 ID 는 `<에셋경로>_ActiveTab` 이라 다시 부르면 기존 탭을 띄운다. **커맨드렛은 탭을 등록하지 않는다**(`!IsRunningCommandlet()`)
→ 헤드리스로는 `None`. EUW 구조 검사는 `ObjectIterator(unreal.Widget)` 로 `<EUW>_C:WidgetTree.*` 템플릿을 훑는다.
**폴더가 junction 인지는 폴더 자체를 볼 것** — `Get-Item <폴더> | Select LinkType` (안 목록만 보고 복사본으로 오판한 적 있음).

**위젯을 파이썬으로 조립 (5.4 실측)**: `unreal.new_object(unreal.TextBlock|Button|EditableTextBox|ComboBoxString|ScrollBox|DetailsView)`
+ `PanelWidget.add_child()` → 슬롯(`set_size(SlateChildSize)` · `set_padding` · `set_vertical_alignment`). EUW 엔
변수 `Root`(VerticalBox) 만 두면 된다. ListView 델리게이트는 `bp_on_entry_initialized` 등 `bp_` 접두.
**델리게이트 `add_callable` 은 기본값 인자도 인자 수로 센다** — `lambda p=x:` 거부 → 클로저 팩토리.

**디테일 뷰 갱신**: CallInEditor 실행 후 강제 새로고침은 없지만 `FPropertyNode::EnsureDataIsValid()` 가 틱마다
배열 크기 변화(`ArraySizeChanged`)를 감지해 다시 그린다 → 버튼에서 배열 프로퍼티를 갱신해 결과 표시로 쓸 수 있다.
파이썬 uproperty 는 항상 `CPF_Edit` 이고 `EditConst` 를 줄 수 없다(메타로도 안 된다).
**에셋 리네임**: `AssetTools.rename_assets([AssetRenameData])` 는 참조하는 에셋까지 고쳐 저장한다(헤드리스 실측:
더티 0, 리디렉터 없음). `FixupReferencers` 는 파이썬 미노출. 클래스 판정은 로드 없이
`AssetRegistry.get_ancestor_class_names(asset_class_path)`.

**파이썬 클래스가 없는 UObject 접근**: `unreal.find_object(None, "/Script/<Module>.Default__<Class>")` 로
CDO 를 잡으면 된다. 단 그때는 프로퍼티 이름이 **C++ 원본 이름**(snake_case 아님). `save_config` 는 없다.

**함정**: 모든 플러그인의 `Content/Python` 이 **같은 `sys.path`** 에 올라간다 →
최상위 패키지에 `tools`/`app`/`utils` 같은 일반 명사 금지 ([[standalone-app-package-collision]] 과 같은 함정).

관련: [[jun-ue-plugin-repo]]
