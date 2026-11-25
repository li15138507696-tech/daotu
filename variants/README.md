# variants 目录说明

主源码 `src/main/java` 是 **1.8.4 通用版**（不读取本体内部类），保持不变。

本目录存放按具体本体版本编译的变体：

## core-10.4

- 基线：git HEAD 的 1.8.2 本体联动版（道痕 / 流派熟练度 / 气运上限 / 本体增益 / 纪事采样）。
- 目标本体：用户提供的 `guzhenrn蛊真人模组本体10.4.jar`，其内嵌
  `META-INF/jarjar/guzhenren-0.1-neoforge-1.21.1.jar`
  （SHA-256 `B6D314D3…A01FE2BC`，与 10.20 的内嵌 jar 相同）。
- 版本：`10.4`（基线为道途 1.8.5 本体联动线），产物 `build/libs/道途-10.4.jar`；
  命名规则统一为「道途 + 适配本体版本」，游戏内显示 `道途 10.4`。
- 与 10.20 的差别只在库层：10.4 没有 `com.guzhenrenlibrary.faction.FactionNpcManager`，
  因此 `shili` 不会被库层写入，宗门见闻簿恒为空；其余字段与过程类完全一致。

命令：

```bash
# 静态兼容审计（哈希、411 个 PlayerVariables 字段、mixin 目标、静态成员、12 个 buff、实体指纹）
python -I tools/audit_core_104.py

# 编译 + 打包
python -I tools/build_core_104.py

# 离线回归（84 项夹具检查）
python -I _crash3/test_optimization.py --source variants/core-10.4/src/main/java
```

运行验证记录见 `build/runtime-core-104.json`，服务端目录 `build/server-104/`（已被 gitignore）。
