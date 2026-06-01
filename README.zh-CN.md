# openkits-skills：让 AI 真正认识你的立创开发板

[English](README.md) · 立创开发板出品

立创开发板 AI 编程助手 skill 集合。让 Claude Code、Codex、Trae、Cursor 等 AI 编程助手理解你的开发板引脚、外设和工具链。

---

## 是什么

每块开发板都有自己的引脚占用、外设配置和工具链规则。这些知识散落在原理图、数据手册和 SDK 文档里，工程师每次上手新板子都要重新翻一遍。openkits-skills 把这些知识整理成结构化的 skill 文件，让 AI 编程助手能直接读懂——知道哪些引脚不能用、对应的 SDK 例程在哪、怎么编译和烧录。

你只需要说一句话，AI 帮你处理剩下的。

## 解决什么问题

接触一块新板子，最耗时的往往不是写业务逻辑：

- **引脚冲突**：板载外设已经占了一堆引脚，随手选一个很可能冲突，而且不报错，只是硬件不工作
- **外设配置繁琐**：SysConfig 时钟树、引脚复用、外设实例，每个都有坑，文档分散
- **例程难找**：SDK 的 `examples/` 目录下几十个子目录，找到对应例程要翻半天
- **编译报错看不懂**：生成代码里的宏名是工具自动生成的，猜不对，改了又改

openkits-skills 的思路是：把这些板级知识沉淀到 skill 文件里，让 AI 一次学会，之后每个用这块板子的人都不用再踩同样的坑。

## 工作原理

```
你说一句话（自然语言需求）
        │
        ▼
  AI 编程助手（Claude Code / Codex / Trae ...）
        │  读取 skill 文件
        ▼
  openkits skill
  ├── 引脚占用表（哪些引脚不能碰）
  ├── 外设参考文档（UART / GPIO / PWM / I2C / SPI / ADC ...）
  └── 工作流规则（Think → Plan → Code → Verify）
        │  调用本地脚本
        ▼
  scaffold.py ──→ 生成工程（.syscfg + 源文件 + 工程配置）
        │
        ▼
  build.py ──→ 工具链编译 ──→ 固件
        │
        ▼
  flash.py ──→ 烧录到开发板
```

整条链路在本地运行，不上传代码，不依赖云端构建。

---

## 可用 Skill

### TI MSPM0 平台

| Skill | 类型 | 说明 |
|-------|------|------|
| [mspm0-ccs](skills/mspm0-ccs/) | 平台 | MSPM0 SysConfig/DriverLib 通用规则 |
| [mspm0kit-tianqiaoxing](skills/mspm0kit-tianqiaoxing/) | 板卡 | 天巧星 MSPM0G3519 开发板 |
| [mspm0kit-tianmengxing](skills/mspm0kit-tianmengxing/) | 板卡 | 天猛星 MSPM0G3507 开发板 |

### 其他平台

待添加：STM32 / ESP32 / GD32 / Rockchip / K230 / RP2350 / CW32 / 瑞萨 / FPGA / SF32LB52

### 实际效果示例（天猛星 MSPM0G3507）

```
你：帮我做一个 UART0 调试串口工程，115200 波特率

AI：我来创建这个工程：
    - 工程名：uart_debug
    - 模板：uart_rw_multibyte_fifo_poll（SDK 官方例程）
    - 引脚：PA10(TX) / PA11(RX)，已连接板载 CH340
    - 时钟：80 MHz HFXT
    确认后开始生成？

你：确认

AI：[scaffold.py uart_debug uart_rw_multibyte_fifo_poll]
    [cleanup.py → build.py]
    编译成功：uart_debug/Debug/uart_debug.out
    烧录：python scripts/flash.py uart_debug
```

---

## 安装

### 推荐：npx skills（支持 28+ agent）

**GitHub（国际）：**

```bash
# 安装单个板卡 skill
npx skills add lckfb/openkits-skills -s mspm0kit-tianmengxing -a claude-code

# 安装整个平台的 skill
npx skills add lckfb/openkits-skills -s mspm0-ccs mspm0kit-tianmengxing -a claude-code

# 安装到多个 agent
npx skills add lckfb/openkits-skills -s mspm0kit-tianmengxing -a claude-code codex trae
```

**Gitee 镜像（国内）：**

```bash
# 安装天猛星
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0kit-tianmengxing -a claude-code

# 安装天巧星
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0kit-tianqiaoxing -a claude-code

# 安装 MSPM0 通用平台 skill
npx skills add https://gitee.com/lcsc/openkits-skills.git -s mspm0-ccs -a claude-code
```

安装过程中选择 **Global（全局）**，然后输入 `yes` 确认。

详细安装步骤：[Claude Code](https://blog.hdochub.com/article/253.html) · [Codex CLI](https://blog.hdochub.com/article/254.html) · [Trae](https://blog.hdochub.com/article/255.html)

### 手动安装

将 `skills/<skill-name>/` 复制到对应 agent 的 skills 目录：

| Agent | 安装路径 |
|-------|---------|
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` |
| Trae | `~/.trae/skills/<name>/` |
| Cursor | `~/.cursor/skills/<name>/` |

### 配置工具链路径（仅 MSPM0 系列）

MSPM0 系列 skill 需要知道 CCS 和 SDK 的安装位置，首次使用时运行一次：

```bash
# 天猛星
python ~/.claude/skills/mspm0kit-tianmengxing/scripts/setup.py

# 天巧星
python ~/.claude/skills/mspm0kit-tianqiaoxing/scripts/setup.py
```

按提示输入路径（直接回车使用默认值），配置保存在 `config.json`，之后不需要重复配置。其他平台的 skill 不需要这一步。

---

## 卸载

### npx skills

```bash
# 查看已安装的 skill
npx skills list

# 删除指定 skill
npx skills remove mspm0kit-tianmengxing

# 删除全局安装的
npx skills remove mspm0kit-tianmengxing -g

# 删除所有
npx skills remove --all
```

### 手动删除

```bash
rm -rf ~/.claude/skills/mspm0kit-tianmengxing   # Claude Code
rm -rf ~/.agents/skills/mspm0kit-tianmengxing   # Codex
```

---

## 添加新板

1. 确认归属的 MCU 平台，若尚无平台 skill 则先创建（参考 [CLAUDE.md](CLAUDE.md)）
2. 复制 `templates/new-board/` 下的三张模板表，填完后在 `skills/` 下创建板卡目录：

```
skills/<board-name>/
├── SKILL.md              # 含 name、requires、pin 表、工作流
├── scripts/              # scaffold.py、build.py、flash.py
├── peripherals/          # 每个外设一个 .md（gpio.md、uart.md …）
└── examples/             # 板卡独有示例（含 manifest.json）
```

3. 更新上方"可用 Skill"表格

详见完整开发规范：[CLAUDE.md](CLAUDE.md)。

---

## 相关链接

- [环境搭建教程](https://blog.hdochub.com/article/252.html)
- [立创开发板文档中心](https://wiki.lckfb.com)
- [TI MSPM0 SDK](https://www.ti.com/tool/MSPM0-SDK)
