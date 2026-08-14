# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14

# True 면 툴 실행 시마다 해당 툴 패키지를 sys.modules 에서 비우고 다시 임포트한다.
# (마야 쪽 `config.DEV_MODE` + `dev/reloader_v02.py` 와 같은 역할)
# 에디터를 재시작하지 않고 코드를 고쳐가며 작업할 때 켜 둔다. 배포 시 False.
DEV_MODE = True
