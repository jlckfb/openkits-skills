# openkits-skills: Teach AI to Know Your LCSC Dev Board

[中文](README.zh-CN.md) · by LCSC Development Board

AI agent skill collection for LCSC development boards. Teach Claude Code, Codex, Trae, Cursor, and 28+ other AI coding agents to understand your board's pins, peripherals, and toolchain.

---

## What Is This

Every dev board has its own pin assignments, peripheral configurations, and toolchain rules. This knowledge is scattered across schematics, datasheets, and SDK docs — engineers have to dig through it every time they pick up a new board. openkits-skills packages this knowledge into structured skill files that AI agents can read directly: which pins are taken, where the SDK examples are, how to build and flash.

You describe what you want. The AI handles the rest.

## What Problems It Solves

The most time-consuming part of starting with a new board is rarely the business logic:

- **Pin conflicts**: On-board peripherals already occupy a bunch of pins. Picking one at random often causes silent hardware failures — no error, the hardware just doesn't work
- **Peripheral configuration**: Clock trees, pin mux, peripheral instances — each has its own pitfalls and scattered docs
- **Finding examples**: The SDK `examples/` directory has dozens of subdirectories; finding the right one takes time
- **Cryptic build errors**: Generated macro names come from the toolchain, not your code — guessing them wrong means repeated trial and error

openkits-skills captures this board-level knowledge in skill files so the AI learns it once, and every engineer using that board avoids the same traps.

## How It Works

```
You describe what you want (natural language)
        │
        ▼
  AI agent (Claude Code / Codex / Trae ...)
        │  reads skill files
        ▼
  openkits skill
  ├── Pin occupation table (which pins are off-limits)
  ├── Peripheral reference docs (UART / GPIO / PWM / I2C / SPI / ADC ...)
  └── Workflow rules (Think → Plan → Code → Verify)
        │  calls local scripts
        ▼
  scaffold.py ──→ generate project (.syscfg + source + project config)
        │
        ▼
  build.py ──→ toolchain compile ──→ firmware
        │
        ▼
  flash.py ──→ flash to board
```

The entire chain runs locally — no code is uploaded, no cloud build required.

---

## Available Skills

### TI MSPM0 Platform

| Skill | Type | Description |
|-------|------|-------------|
| [mspm0-ccs](skills/mspm0-ccs/) | Platform | MSPM0 SysConfig/DriverLib general rules |
| [mspm0kit-tianqiaoxing](skills/mspm0kit-tianqiaoxing/) | Board | Tianqiaoxing MSPM0G3519 dev board |
| [mspm0kit-tianmengxing](skills/mspm0kit-tianmengxing/) | Board | Tianmengxing MSPM0G3507 dev board |

### Other Platforms

Coming soon: STM32 / ESP32 / GD32 / Rockchip / K230 / RP2350 / CW32 / Renesas / FPGA / SF32LB52

### Example (Tianmengxing MSPM0G3507)

```
You:  Create a UART0 debug project, 115200 baud

AI:   Here's what I'll create:
      - Project: uart_debug
      - Template: uart_rw_multibyte_fifo_poll (SDK official example)
      - Pins: PA10(TX) / PA11(RX), connected to on-board CH340
      - Clock: 80 MHz HFXT
      Confirm to proceed?

You:  Confirm

AI:   [scaffold.py uart_debug uart_rw_multibyte_fifo_poll]
      [cleanup.py → build.py]
      Build succeeded: uart_debug/Debug/uart_debug.out
      Flash: python scripts/flash.py uart_debug
```

---

## Install

### Recommended: npx skills (28+ agents)

```bash
# Install a single board skill
npx skills add lckfb/openkits-skills -s mspm0kit-tianmengxing -a claude-code

# Install all skills for a platform
npx skills add lckfb/openkits-skills -s mspm0-ccs mspm0kit-tianmengxing -a claude-code

# Target multiple agents at once
npx skills add lckfb/openkits-skills -s mspm0kit-tianmengxing -a claude-code codex trae
```

**China mirror (Gitee):**

```bash
# Tianmengxing
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0kit-tianmengxing -a claude-code

# Tianqiaoxing
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0kit-tianqiaoxing -a claude-code

# MSPM0 platform skill
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0-ccs -a claude-code
```

Select **Global** when prompted, then enter `yes` to confirm.

### Manual Install

Copy `skills/<skill-name>/` to the agent's skills directory:

| Agent | Install Path |
|-------|-------------|
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` |
| Trae | `~/.trae/skills/<name>/` |
| Cursor | `~/.cursor/skills/<name>/` |

### Toolchain Path Setup (MSPM0 only)

MSPM0 skills need to know where CCS and the SDK are installed. Run once on first use:

```bash
# Tianmengxing
python ~/.claude/skills/mspm0kit-tianmengxing/scripts/setup.py

# Tianqiaoxing
python ~/.claude/skills/mspm0kit-tianqiaoxing/scripts/setup.py
```

Follow the prompts (press Enter to accept defaults). Settings are saved to `config.json` and don't need to be repeated. Other platform skills don't require this step.

---

## Uninstall

### npx skills

```bash
# List installed skills
npx skills list

# Remove a specific skill
npx skills remove mspm0kit-tianmengxing

# Remove global install
npx skills remove mspm0kit-tianmengxing -g

# Remove all
npx skills remove --all
```

### Manual

```bash
rm -rf ~/.claude/skills/mspm0kit-tianmengxing   # Claude Code
rm -rf ~/.agents/skills/mspm0kit-tianmengxing   # Codex
```

---

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

---

## Links

- [Environment setup guide](https://blog.hdochub.com/article/252.html)
- [LCSC Dev Board Docs](https://wiki.lckfb.com)
- [TI MSPM0 SDK](https://www.ti.com/tool/MSPM0-SDK)
