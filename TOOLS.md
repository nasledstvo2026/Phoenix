# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## 🤖 Триггеры агентов

| Триггер | Агент (agentId) | Назначение |
|---------|-----------------|------------|
| **Федор** | `fz425-agent` | Консультант по 425-ФЗ (вызывает fz425-verifier) |

### Как добавить нового агента
1. Создать агента в `openclaw.json` → `agents.list`
2. Добавить в `tools.agentToAgent.allow`
3. Присвоить имя-триггер → записать в эту таблицу
4. Обновить `AGENTS.md` если нужно (новый агент может иметь свою логику)

## Инфраструктура

### GitHub Pages — nasledstvo
- Репозиторий: `nasledstvo2026/nasledstvo`
- Ветка деплоя: master → GitHub Actions → gh-pages (workflow: .github/workflows/deploy-pages.yml)
- Домен: `https://nasledstvo2026.github.io/nasledstvo/`
- Remote: `origin` (git@github.com:nasledstvo2026/nasledstvo.git)

### GitHub Pages — Phoenix
- Репозиторий: `nasledstvo2026/Phoenix` (локально: ~/phoenix)
- Ветка деплоя: `main` (классический GH Pages, без workflow)
- Домен: `https://nasledstvo2026.github.io/Phoenix/`
- Remote: `origin` (git@github.com:nasledstvo2026/Phoenix.git)

### VPS
- Имя: vps2
- Хост: vm-low4-8
- IP: 213.171.25.85
- ОС: Linux 6.8.0-136-generic (x64)
- Node: v22.23.1
- Gateway: OpenClaw

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
