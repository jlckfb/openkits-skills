# openkits-skills

立创开发板 AI 编程助手 skill 集合。让 AI 编程助手（Claude Code、Codex、Trae、Cursor 等）理解你的开发板引脚、外设和工具链。

## 安装

### 推荐：npx skills（支持 28+ agent）

```bash
# 安装单个板卡 skill
npx skills add LaoGuaiGe/openkits-skills -s mspm0kit-tianqiaoxing

# 安装整个平台的 skill
npx skills add LaoGuaiGe/openkits-skills -s mspm0-ccs mspm0kit-tianqiaoxing

# 指定目标 agent
npx skills add LaoGuaiGe/openkits-skills -s mspm0kit-tianqiaoxing -a claude-code codex trae
```

### 手动安装

将 `skills/<skill-name>/` 复制到对应 agent 的 skills 目录：

| Agent | 安装路径 |
|-------|---------|
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` |
| Trae | `~/.trae/skills/<name>/` |
| Cursor | `~/.cursor/skills/<name>/` |

## 可用 Skill

### TI MSPM0 平台

| Skill | 类型 | 说明 |
|-------|------|------|
| [mspm0-ccs](skills/mspm0-ccs/) | 平台 | MSPM0 SysConfig/DriverLib 通用规则 |
| [mspm0kit-tianqiaoxing](skills/mspm0kit-tianqiaoxing/) | 板卡 | 天巧星 MSPM0G3519 开发板 |

### 其他平台

待添加：STM32 / ESP32 / GD32 / Rockchip / K230 / RP2350 / CW32 / 瑞萨 / FPGA / SF32LB52

## 开发

参见 [CLAUDE.md](CLAUDE.md)。
