# openkits-skills

[中文](README.zh-CN.md)

LCSC development board AI agent skill collection. Teach AI coding agents (Claude Code, Codex, Trae, Cursor, and 28+ others) to understand your board's pins, peripherals, and toolchain.

## Install

### Recommended: npx skills (28+ agents supported)

```bash
# Install a single board skill
npx skills add lckfb/openkits-skills -s mspm0kit-tianqiaoxing -a claude-code

# Install all skills for a platform
npx skills add lckfb/openkits-skills -s mspm0-ccs mspm0kit-tianqiaoxing -a claude-code

# Target specific agents
npx skills add lckfb/openkits-skills -s mspm0kit-tianqiaoxing -a claude-code codex trae
```

### Manual Install

Copy `skills/<skill-name>/` to the agent's skills directory:

| Agent | Install Path |
|-------|-------------|
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` |
| Trae | `~/.trae/skills/<name>/` |
| Cursor | `~/.cursor/skills/<name>/` |

## Uninstall

### npx skills

```bash
# List installed skills
npx skills list

# Remove a specific skill
npx skills remove mspm0kit-tianqiaoxing

# Remove global install
npx skills remove mspm0kit-tianqiaoxing -g

# Remove all
npx skills remove --all
```

### Manual

```bash
rm -rf ~/.claude/skills/mspm0kit-tianqiaoxing   # Claude Code
rm -rf ~/.agents/skills/mspm0kit-tianqiaoxing   # Codex
```

## Available Skills

### TI MSPM0 Platform

| Skill | Type | Description |
|-------|------|-------------|
| [mspm0-ccs](skills/mspm0-ccs/) | Platform | MSPM0 SysConfig/DriverLib general rules |
| [mspm0kit-tianqiaoxing](skills/mspm0kit-tianqiaoxing/) | Board | Tianqiaoxing MSPM0G3519 dev board |
| [mspm0kit-tianmengxing](skills/mspm0kit-tianmengxing/) | Board | Tianmengxing MSPM0G3507 dev board |

### Other Platforms

Coming soon: STM32 / ESP32 / GD32 / Rockchip / K230 / RP2350 / CW32 / Renesas / FPGA / SF32LB52

## Add a New Board

1. Identify the MCU platform. If no platform skill exists, create one first (see [CLAUDE.md](CLAUDE.md)).
2. Copy `templates/new-board/`, fill in the 3 template sheets, and create the skill directory under `skills/`:

```
skills/<board-name>/
├── SKILL.md              # name, requires, pin table, workflow
├── scripts/              # scaffold.py, build.py, flash.py
├── peripherals/          # one .md per peripheral (gpio.md, uart.md, …)
└── examples/             # board-specific examples (with manifest.json)
```

3. Update the "Available Skills" table above.

Full spec: [CLAUDE.md](CLAUDE.md).
