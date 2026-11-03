# 道途试炼 Implementation Plan

> 执行方式：在当前会话逐项完成。项目目录没有 Git 元数据；改动落在用户指定的道途附属目录。

**目标：** 为道途加入服务端权威的战斗、探索、修炼试炼，包含每世进度、一次性历练奖励和 M 界面入口。

**架构：** 试炼类型集中在 DaotuTrial，本世存档沿用 DaotuRun。DaotuTrialService 验证接取、累计现有玩法事件、原子结算半个当前抽选门槛的历练，并经现有状态包同步。M 界面在当前滚动列表中显示进度与选择项。

**技术：** Java 21、Minecraft 1.21.1、NeoForge 21.1.263、现有自定义网络载荷、玩家 NBT、项目离线 javac 与 JAR 打包脚本。

## 全局约束

- 保留五选一锁定、每十抽特殊选择、现有抽选上限和转世行为。
- 接取及进度都以服务端为准；客户端仅发送 runId、里程碑、试炼 id。
- 试炼状态保存在 daotu/run，转世通过现有 run 重置一起清空。
- 不加道具、生物、贴图、配方、外部依赖，也不声称复刻原著。
- 内容版本按项目规则升至 1.7.0。
- 不运行测试套件；使用现有脚本编译并打包。

---

### Task 1：类型与本世存档

**文件：**
- 新建 src/main/java/net/guzhenren/daotu/DaotuTrial.java
- 新建 src/main/java/net/guzhenren/daotu/DaotuTrialService.java
- 修改 src/main/java/net/guzhenren/daotu/DaotuRun.java

**接口：**
- DaotuTrial.Type 定义 combat（击杀 8 只敌对生物）、exploration（接取后进入 2 个不同群系）、meditation（合格打坐 180 秒），提供稳定 id、名称、说明和安全 byId。
- DaotuTrial.Snapshot 包含 ready、milestone、nextMilestone、type、progress、target、completed。
- DaotuRun.trialSnapshot(Player) 按已完成抽选数与上限派生下一个可接里程碑。
- DaotuRun.acceptTrial(Player, int milestone, String type) 仅接受下一个已解锁里程碑，并拒绝并行试炼。
- DaotuRun.advanceTrial(Player, int milestone, int delta, String biome) 更新有效进度；探索群系在单个试炼中去重，返回是否改变与是否完成。
- 完成标记、奖励标记和 thresholdOf(player) / 2 历练在一次 NBT 更新中落盘，防止重复发奖。

- [x] 添加稳定试炼类型、目标、显示文本和状态快照。
- [x] 添加本世已领取里程碑、试炼类型、进度、访问群系、完成与发奖状态的读写。
- [x] 强制顺序领取、抽数门槛、单试炼、合法类型和满上限时不开放新试炼。
- [x] 进度限制在目标内，探索群系仅对当前有效探索试炼去重。
- [x] 原子地标记完成并把奖励并入现有历练池。

### Task 2：服务端事件与网络

**文件：**
- 新建 src/main/java/net/guzhenren/daotu/net/DaotuTrialPayload.java
- 修改 src/main/java/net/guzhenren/daotu/DaotuTrialService.java
- 修改 src/main/java/net/guzhenren/daotu/DaotuLiLian.java
- 修改 src/main/java/net/guzhenren/daotu/DaotuNet.java
- 修改 src/main/java/net/guzhenren/daotu/net/DaotuStatePayload.java
- 修改 src/main/java/net/guzhenren/daotu/DaotuMod.java

**接口：**
- DaotuTrialService.accept(ServerPlayer, runId, milestone, type) 校验接取请求。
- DaotuTrialService.onKill(ServerPlayer, LivingEntity)、onBiome(ServerPlayer, String)、onMeditationSecond(ServerPlayer, boolean) 只记录接取后的事件。
- DaotuTrialPayload 是仅含 runId、milestone、试炼 id 的 C2S 包，注册在现有 registrar。
- DaotuStatePayload 新增 DaotuTrial.Snapshot，编解码字段顺序一致。
- DaotuNet.send 从服务端试炼状态创建快照。

- [x] 注册 C2S 包，拒绝旧转世、旧里程碑、非法类型、重复接取和满上限接取。
- [x] 只计玩家最后一击击杀的 Monster；不改既有击杀历练计算。
- [x] 从现有每秒采样累计不同群系和合格打坐秒数。
- [x] 每个有效事件立即存档；战斗/探索变化即时推界面，打坐每 5 秒同步，完成时立即同步。
- [x] 完成时播报一次、调用既有抽选流程并刷新状态，不突破上限。
- [x] 在 S2C 状态包与发送器中添加试炼快照。

### Task 3：M 界面、说明、版本与 JAR

**文件：**
- 修改 src/main/java/net/guzhenren/daotu/client/DaotuViewScreen.java
- 必要时修改 src/main/resources/assets/daotu/lang/zh_cn.json
- 修改 docs/道途使用说明.md
- 修改 version.properties
- 修改 src/main/resources/META-INF/neoforge.mods.toml
- 新建 docs/2026-10-27-daotu-trials.md
- 构建 build/libs/daotu-1.7.0.jar

**接口：**
- 界面只读 DaotuStatePayload.trial()；点击时发送 DaotuTrialPayload。
- 试炼选项行复用虚拟列表；命中区仍只在 layout() 中分配。
- 玩家说明写明解锁、目标、历练奖励、存档与上限规则。

- [x] 在现有列表属性记录前加入试炼区，展示进度/完成状态；仅 ready 时显示三种选择。
- [x] layout() 分配试炼行命中区；drawRows() 绘制悬停状态；点击发送 runId 和里程碑。
- [x] 更新玩家说明与实现记录，内容与代码一致。
- [x] 两个版本源设为 1.7.0，更新 mod 描述以反映现有玩法。
- [x] 全量编译 49 个 Java 源文件，按项目离线类路径打包全部 class 与资源，并核对 JAR 路径及内嵌版本。

## 自查

- 覆盖三种试炼、接取后计数、存档、一次奖励、服务器权威、M 界面、上限、转世、玩家说明、版本与 JAR。
- 不新增道具、生物、图片、配方、依赖或已删除势力系统。
- 项目无 .git，计划不包含提交或 worktree 操作。
- 只编译打包，不运行测试套件。
