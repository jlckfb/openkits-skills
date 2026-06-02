# 新增板卡 Skill 指南

本目录包含三个信息收集模板，用于在让 AI 制作板卡 skill 前准备必要的板级知识。

---

## 第一步：收集板卡信息

在动手前，准备以下资料：

- 开发板原理图（或引脚功能标注表）
- 芯片型号、封装、Flash/SRAM 大小
- 使用的 IDE / SDK / 工具链版本
- 调试器类型（J-Link / XDS110 / CMSIS-DAP）

---

## 第二步：填写三个模板

复制本目录下的三个文件到一个临时工作目录，按说明填写：

| 文件 | 填写内容 |
|------|---------|
| `pin_occupation_table.md` | 哪些引脚不可用、哪些被板载外设占用、哪些空闲 |
| `peripherals_list.md` | 板载外设清单（LED/按键/OLED/IMU/WS2812/蜂鸣器等），填芯片型号和引脚 |
| `extra_notes.md` | 芯片封装、时钟、调试器、与同平台其他板卡的差异 |

填写完成后告诉 AI："三个文件填完了，帮我制作 skill"。

---

## 第三步：AI 生成 skill

AI 会基于模板内容，在 `skills/<board-name>/` 下生成：

```
skills/<board-name>/
├── SKILL.md              # AI 行为规则：pin 表 + 工作流 + 外设约束
├── scripts/
│   ├── setup.py          # 工具链路径配置
│   ├── scaffold.py       # 工程生成
│   ├── build.py          # 编译
│   ├── flash.py          # 烧录
│   ├── cleanup.py        # 构建前清理
│   └── serial_console.py # 串口监视
└── peripherals/
    ├── gpio.md
    ├── uart.md
    └── ...               # 每个有对应外设就建一个文件
```

命名规范：
- MSPM0 系列沿用 `mspm0kit-<boardname>`
- 立创其他板卡用 `lckfb-<chipmodel>`，如 `lckfb-stm32f103c8t6`

---

## 第四步：测试 skill

安装生成好的 skill 到本地，至少完成以下测试：

- [ ] 创建一个 LED 闪烁工程，编译通过
- [ ] 烧录成功，硬件验证 LED 实际闪烁
- [ ] 创建一个带按键中断的工程，验证中断响应
- [ ] 如有板载 UART，验证串口输出

测试中记录遇到的每个问题（现象 / 根因 / 修复方法），格式参考 `skill_test_log.md`。

---

## 第五步：提交

提交 PR 时需要包含：

### 必须提交

- `skills/<board-name>/` 完整目录
- 更新 `README.md` 和 `README.zh-CN.md` 的"可用 Skill"表格

### 建议提交

- 一份测试日志（`skill_test_log.md`），记录测试结果和遇到的坑
  - 放在 `skills/<board-name>/references/` 下，或作为 PR description 附上

### PR description 模板

```
## 新增 <board-name> 板卡 Skill

**芯片**：<chip>  
**平台**：<platform skill 依赖>  
**测试环境**：<IDE 版本 / SDK 版本 / 调试器>

### 已验证功能
- [ ] LED 闪烁
- [ ] 按键中断
- [ ] UART 输出
- [ ] ...

### 已知问题 / 限制
- ...
```

---

## 参考

已有 skill 实现参考：
- 平台 skill：`skills/mspm0-ccs/`
- 简单板卡：`skills/mspm0kit-tianmengxing/`
- 完整板卡（含 OLED/IMU/WS2812）：`skills/mspm0kit-tianqiaoxing/`
