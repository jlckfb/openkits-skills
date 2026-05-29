# openkits-skills 开发规范

立创开发板 AI 编程助手 skill 集合。每个 skill 是一个独立的 `skills/<name>/` 目录，可通过 `npx skills` 或手动复制安装。

## 目录结构

```
skills/
├── <platform>-<toolchain>/      # 平台 skill（跨板共享的工具链/驱动库知识）
│   ├── SKILL.md
│   ├── scripts/                 # 平台公共脚本
│   ├── references/              # 平台参考文档
│   └── examples/                # 平台通用示例
│
└── <board-name>/                # 板卡 skill（pin 表 + 板级外设）
    ├── SKILL.md                 # frontmatter 中必须声明 requires
    ├── scripts/                 # 板级脚本（调用平台脚本）
    ├── peripherals/             # 板级外设 pin 映射文档
    ├── examples/                # 板卡独有示例
    └── config.json              # 板级路径配置（由 setup.py 生成）
```

## 命名规范

- **平台 skill**: `{mcu}-{toolchain}`，如 `mspm0-ccs`、`stm32-hal`、`esp32-idf`、`rk-linux`
- **板卡 skill**: `lckfb-{chip}`，如 `lckfb-stm32f103c8t6`（已有 mspm0 系列保留 `mspm0kit-` 前缀）

## SKILL.md 规范

每个 `SKILL.md` 必须有 frontmatter：

```yaml
---
name: <skill-name>          # 唯一标识，与目录名一致
description: <one-line>     # 一句话描述，会出现在 skill 列表中
requires: [<dependency>]    # 板卡 skill 必须声明依赖的平台 skill
---
```

## 板卡 skill 模板

```
skills/<board-name>/
├── SKILL.md                 # name + requires + pin 表 + 工作流
├── config.json              # 工具链路径（运行时由 setup.py 生成）
├── peripherals/              # 每个外设一个 .md（pin 映射 + 示例索引）
│   ├── gpio.md
│   ├── uart.md
│   ├── spi.md
│   └── ...
├── examples/                # 板卡独有示例（含 manifest.json）
├── scripts/                 # 板级脚本
│   ├── scaffold.py
│   ├── build.py
│   └── flash.py
└── references/              # 板级参考（硬件校验笔记等）
```

## 添加新板

1. 确认归属的 MCU 平台，如果没有对应平台 skill，优先创建平台 skill
2. 在 `skills/` 下按命名规范创建板卡目录
3. 复制同平台最近板卡的目录作模板
4. 更新 pin 表、外设文档、示例
5. 如需新的平台 skill，参考 `skills/mspm0-ccs/` 结构
