# Junction 이란 — 폴더를 복사하지 않고 연결하는 법

> 이 저장소의 설치 안내([README](../README.md), [설계 가이드 6장](00_UE_Tool_Plugin_Guide.md))에서
> 계속 나오는 `mklink /J` 가 무엇인지 정리한 문서.

---

## 한 줄 정의

**Junction = "폴더용 바로가기, 단 윈도우가 진짜 폴더로 착각하는 것"**

윈도우 파일 시스템(NTFS)의 기능이다. A 폴더를 만들지만 그 안을 들여다보면 실제로는 B 폴더의 내용이 보인다.

```
C:\UE_Plugins\JUNTools   ← 겉보기엔 폴더 (junction)
        │
        └─ 실제 내용은 이쪽
           C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE   ← 진짜 폴더 (git 저장소)
```

핵심은 **사본이 아니라는 것**이다. 파일은 세상에 하나뿐이고, 보이는 입구만 두 개다.

---

## 왜 쓰는가 — 복사와 무엇이 다른가

플러그인을 프로젝트에 **복사**하면 이렇게 된다.

```
JUN_UE\Content\...                     (원본, git 저장소)
MANUProject\Plugins\JUN\Content\...    (사본 — 완전히 별개의 파일)
```

- 원본에서 툴을 고쳐도 **사본은 그대로다** → 다시 복사해야 한다
- 프로젝트가 3개면 고칠 때마다 3번 복사
- 시간이 지나면 **어느 쪽이 최신인지 알 수 없어진다**
- 사본에서 급하게 고친 내용은 git 에 안 남고 다음 복사 때 덮여서 사라진다

junction 을 쓰면 사본이 존재하지 않는다.

```
C:\UE_Plugins\JUNTools  ──링크──▶  JUN_UE  (git 저장소)
```

언리얼은 `C:\UE_Plugins\JUNTools` 를 평범한 플러그인 폴더로 인식해 읽지만,
실제로 읽는 것은 git 저장소 원본이다. 그래서:

- 에디터에서 코드 고치고 → `Tools > JUN > Reload JUN Tools` → **끝**. 복사 단계가 없다
- `git pull` 을 받으면 즉시 반영된다
- 어느 프로젝트에서 무엇을 고쳤든 전부 같은 원본이라 갈라질 일이 없다

---

## 바로가기(.lnk) / 복사와 비교

| | 바로가기 (`.lnk`) | **Junction** | 복사 |
|---|---|---|---|
| 정체 | 탐색기가 해석하는 **파일** | 파일 시스템 수준의 **폴더** | 별개의 파일 묶음 |
| 다른 프로그램이 폴더로 인식? | ❌ 못 함 | ✅ 함 | ✅ |
| 파일 중복 | 없음 | 없음 | **있음** |
| 원본 수정이 즉시 반영? | - | ✅ | ❌ |
| 관리자 권한 | - | 불필요 | - |

바로가기는 탐색기에서 더블클릭할 때만 동작하는 "안내판"이라 언리얼 같은 프로그램은
그냥 정체불명 파일로 본다. junction 은 **파일 시스템이 직접 처리**하므로 어떤 프로그램이 열어도
진짜 폴더로 보인다. 그래서 언리얼이 속아 넘어간다.

> **symbolic link (`mklink /D`) 와는?**
> 거의 같은 일을 하지만 심볼릭 링크는 **관리자 권한(또는 개발자 모드)** 이 필요하고
> 네트워크 경로를 가리킬 수 있다. 로컬 폴더를 잇는 용도라면 **권한이 필요 없는 junction 이 편하다.**

---

## 명령어

### 만들기

```powershell
# /J 가 junction. 순서: mklink /J <만들 링크> <가리킬 진짜 폴더>
cmd /c mklink /J "C:\UE_Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"
```

> PowerShell 에는 `mklink` 가 없다(cmd 내장 명령). 그래서 `cmd /c` 를 앞에 붙인다.

### 확인

```powershell
Get-Item "C:\UE_Plugins\JUNTools" | Select-Object Name, LinkType, Target
```

`LinkType` 이 `Junction` 으로, `Target` 이 원본 경로로 나오면 정상이다.

### 지우기 ⚠️

**링크만 지워야지 원본까지 지우면 안 된다.**

```powershell
# 안전 — 링크만 제거, 원본은 그대로
[System.IO.Directory]::Delete("C:\UE_Plugins\JUNTools", $false)

# 위험 — 도구/버전에 따라 링크를 따라 들어가 원본 내용까지 지울 수 있다
Remove-Item -Recurse -Force "C:\UE_Plugins\JUNTools"
```

원본이 git 저장소이므로 잘못 지우면 커밋하지 않은 작업이 날아간다.
**junction 을 정리할 때는 항상 위쪽 방법을 쓴다.**

---

## 이 저장소에서 junction 이 등장하는 자리

### 1. 플러그인 스테이징 (권장 설치 방식)

```powershell
New-Item -ItemType Directory -Force "C:\UE_Plugins"
cmd /c mklink /J "C:\UE_Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"
setx UE_ADDITIONAL_PLUGIN_PATHS "C:\UE_Plugins"
```

`C:\UE_Plugins` 는 **프로젝트 바깥**이다. 그래서 회사 프로젝트 폴더를 전혀 건드리지 않는다.

### 2. 특정 프로젝트에만 붙일 때

```powershell
cmd /c mklink /J "<Project>\Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"
```

---

## ⚠️ 버전 관리와 junction

**`MANUProject\Plugins\` 안에 junction 을 걸면 SVN 이 링크를 따라 들어가 원본 저장소 전체를
커밋하려 들 수 있다.** Perforce 도 마찬가지다.

그래서 설치 안내에서 `Plugins/` 안이 아니라 `C:\UE_Plugins` 라는 **바깥 폴더**에 junction 을 걸고
환경변수(`UE_ADDITIONAL_PLUGIN_PATHS`)로 알려주는 방식을 1순위로 권한다.

굳이 `Plugins/` 안에 둬야 한다면 **junction 을 만들기 전에** `svn:ignore` / `.gitignore` 에
먼저 등록할 것.

---

## 참고

같은 방식이 마야 쪽에서도 쓰이고 있다 — `.claude/memory` 가 저장소와 junction 으로 연결되어 있어
PC 를 옮겨도 메모리가 따라간다. 새로운 개념이 아니라 이미 쓰고 있던 도구다.
