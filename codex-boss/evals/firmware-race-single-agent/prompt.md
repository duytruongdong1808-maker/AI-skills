---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Repo D:\HCMUT\HK261\IOT\smart-classroom-iot. Bên firmware/uno-control/src/espnow_rx.cpp thỉnh thoảng nhận packet bị hỏng khi uno-sensor gửi dồn dập, nghi là race giữa callback ESP-NOW và loop(). Để codex xử lý giúp mình.
