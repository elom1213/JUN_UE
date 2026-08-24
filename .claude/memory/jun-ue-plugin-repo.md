---
name: jun-ue-plugin-repo
description: 언리얼 툴이 마야 repo 가 아니라 별도 JUN_UE 여야 하는 이유와, 푸시 대상이 다르다는 함정
metadata:
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
---

**구조와 규칙 본문은 저장소 루트 `CLAUDE.md` 에 있다.** 이 메모는 그 배경과 함정을 남긴다.

## 왜 마야 repo 에 섞지 않았나 (2026-08-14 분리)

언리얼 플러그인은 **배치 경로가 고정**이고(`<Project>/Plugins/<Name>/`),
**엔진 버전이라는 버전 축이 하나 더** 붙으며, 이식이 **submodule / junction 단위**라
마야 파이썬 트리에 섞을 수 없다.

## 함정 — 푸시 대상이 다르다

- `JUN_UE` -> `origin` 의 `main`
- `Maya_Python` -> `Dnable_repo` 의 `dev`

**마야 저장소의 기본 푸시 대상 규칙이 여기엔 적용되지 않는다.** 습관으로 `Dnable_repo` 를 치지 말 것.
푸시 자체는 그 턴에 요청이 있을 때만 (전역 규칙 2장).

## 라우팅

**언리얼 에디터 툴 얘기가 나오면 `Maya_Python/JUN_All` 이 아니라 여기로 온다.**
다른 저장소 세션에서 요청이 나와도 마찬가지다.

플러그인 식별자는 `JUNTools.uplugin` (= 에셋 마운트 경로 `/JUNTools/`, **변경 금지**).
설계 근거와 함정은 `Docs/00_UE_Tool_Plugin_Guide.md` 에 정리돼 있으니 작업 전 열어볼 것.

관련: [[unreal-python-tool-verify]]
