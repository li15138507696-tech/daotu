<!-- Path: FILL-SPEC.md -->
# Agent B 编码交接规范

## 1. 目标与验收标准

在不改现有方法签名、不改 1.5.2 版本号、不写天命字段的前提下，填充 `chronicle/` 的 12 个方法体，使三种纪事可在服务端独立保存和查询。当前交付是架构骨架：事件体无逻辑、快照/仓储/计算返回空或 false、查询返回 0；不要把它当成业务完成。

固定 Minecraft 1.21.1、NeoForge 21.1.249、Java 21；Gradle 声明锁定 9.2.1、net.neoforged.moddev 2.0.144，但本项目验收只走现有 Python 编译/打包工具。所有 Java UTF-8 无 BOM。

交付完成要求：纯模块满足下述示例；两位玩家数据隔离；Clone、重登和转世不丢跨世条目；适配失败不生成错误存档；服务端能运行 `/daotu-chronicle`，不抢开窍弹窗；本体及天命字段在仅触发新模块前后完全不变。已有道途自身的道痕/流派写入冲突是 PLAN 的 R1，不可因新模块隔离便宣称整个模组已无冲突。

## 2. 文件所有权表

前缀 `J=src/main/java/net/guzhenren/daotu/chronicle/`。

| 文件 | 所有权/状态 | 可修改边界 |
| --- | --- | --- |
| PLAN.md、FILL-SPEC.md | 架构阶段已完成 | 编码结论变化时同步证据，不降低已声明约束 |
| J/ChronicleModels.java | 已完成的数据定义 | 保持 record 名称、字段顺序、字段类型；不添加本体可变引用 |
| J/ChronicleTables.java | 已完成的数据表 | 10/40/80 贡献、100/1000/5000 声望；调参需说明，不声称本体常量 |
| J/CoreVersionAdapter.java | 已完成接口 | 签名固定；只读边界不能新增写本体接口 |
| J/ChronicleModule.java | 已完成抽象契约 | 签名固定，纯计算边界不变 |
| J/ChronicleRepository.java | 已完成仓储接口 | 签名固定；保留 expectedRevision 语义 |
| J/Core1020Adapter.java | 等待填充：1 个方法 | 按审计字段只读采样，不反射猜字段 |
| J/FactionJournalModule.java | 等待填充：1 个方法 | 只生成宗门见闻的新状态 |
| J/MeritArchiveModule.java | 等待填充：1 个方法 | 只生成贡献基线/峰值/档案的新状态 |
| J/ReputationJournalModule.java | 等待填充：1 个方法 | 只生成声望基线/峰值/纪事的新状态 |
| J/NbtChronicleRepository.java | 等待填充：3 个方法 | 仅 daotu_chronicle 根，不写 SQLite/YAML |
| J/ChronicleCoordinator.java | 依赖装配已完成；2 个方法待填 | 按顺序聚合模块，单次提交及只读查询 |
| J/ChronicleEvents.java | 构造器已完成；3 个监听方法待填 | 服务端过滤、节流、Clone 分发 |
| ../DaotuMod.java | 主类注册已完成 | 保留旧构造器/方法/协议；新增注册不重复，不添加 Bukkit TabCompleter |
| build.gradle/settings.gradle/gradle.properties | 锁定声明已完成；Gradle 未执行 | 不替换用户锁定坐标，不生成 wrapper 后擅自运行 |
| _crash3/javac_check.py | 编译工具已调整 | 固定 249 平台 jar，指定内层 jar，JDK 21 source/target 21 |
| _crash3/audit_1020.py、verify_architecture.py | 证据工具已完成 | 允许扩展检测，不伪造检查结果 |
| 其余原有 32 个 Java 文件 | 原样保留、无本轮待填方法 | 不把既有业务改成占位；R1 修复需单独设计数据迁移 |
| version.properties、src/main/resources/META-INF/neoforge.mods.toml | 禁改版本；本轮整文件保持 | 不用 bump_version/bump_toml，不绕过版本交叉检查 |

## 3. 公共模型及全局不变量

所有类型在 `ChronicleModels` 下，定义以源文件为准：

- `CoreSnapshot(UUID playerId,long gameTick,int runId,boolean opened,String faction,String identity,double contribution,double reputation)`：同一 tick、同一玩家的不可变只读输入。faction 对应 shili、identity 对应 shenfen；不从字符串猜 ID。
- `FactionJournal(Set<String> discoveredPairs,String lastFaction,String lastIdentity,long lastObservedTick)`：组合去重，最多 128 项；每项编码必须无歧义。最后观测值与已收集历史区分。
- `MeritArchive(double lastObserved,double peakObserved,Set<String> unlockedEntries,long lastObservedTick)` 与 `ReputationJournal(...)`：分别代表观测值、本局峰值、跨世解锁集合及基线时刻。
- `ChronicleState(UUID playerId,int schema,long revision,int runId,FactionJournal faction,MeritArchive merit,ReputationJournal reputation)`：schema=1；初建 revision=0；根 `daotu_chronicle`。
- `ModuleDecision(String moduleId,ChronicleState nextState,List<String> entries)`：纯候选；entries 是本次新增条目 ID，不是发放物品指令。moduleId 固定为各模块 ID 常量。
- `Milestone(String id,double threshold,String displayName)`：本附属设计表，不是本体 API 或合成配方。

所有参数非空、集合不可变、成员非空；无 NaN/Infinity；revision/runId 非负（save 的 expectedRevision 可为 -1）；gameTick 非负。每个 lastObservedTick=-1 表示尚无基线，其余非负。字符串各限制 128 个 Unicode 码点；超长快照拒绝，不用截断后碰撞。空字符串允许，不替换本体原值；缺失与类型不匹配由适配/仓储拒绝。

集合上限：discoveredPairs 128 项；merit/reputation 的集合只允许各自数据表 3 个 ID；ModuleDecision.entries 至多 128 项，且必须是这次新解锁集合的差集。宗门条目 ID 使用 `faction_journal:` 加无歧义组合编码，功绩/声望用表中 ID。不接受任意字符串作为奖励指令。

记录型 POJO 构造器没有业务校验；适配器、仓储及协调器承担校验，纯模块可拒绝不合法输入。不得为了满足不可变契约去修改调用者传入的集合。

新模块本体写集合必须为空；也不写 `daotu`、`tianfu`、tizhi、daohen_*、dahen_*、liupai_*、v2_*。禁止调用 `DaotuSpecial.grant`、`DaotuTalentApply.apply`、`DaotuGrowthApply.addDaohen/addLiupai/refreshTitles` 或本体任务奖励 procedure。禁止发 buff、物品、属性 modifier；本轮玩法收益仅为独立纪念条目。

## 4. 每个待填文件的接口契约、标记与验收

以下恰为 12 个 Java 源码中的 `[TODO: Agent B]` 标记；“位置”用文件与方法唯一标识，精确行号另见 verification.json。

### Core1020Adapter.java — read

签名 `public Optional<CoreSnapshot> read(ServerPlayer player)`，实现 `CoreVersionAdapter`。player 是非空在线玩家，须在服务端主线程；线程错误抛 IllegalStateException。预期的不支持版本、附件不可用、字符串/数值不合法返回 Optional.empty，记录可诊断日志且限频；不能吞掉所有 Throwable。

标记：只读 shili、shenfen、GongXianZhi、mingsheng 与 kaiqiao，校验线程及有限数值后生成快照。

取得 PLAYER_VARIABLES 后仅复制上述四字段；gameTick 来自服务端世界时间；runId 用现有只读 `DaotuRun.runId(player)`。kaiqiao objective 缺失或分数缺失为 opened=false，**不调用 getOrCreatePlayerScore**。确切查询 API 需从 1.21.1 本地 jar javap 后再用，禁止凭其他版本记忆猜签名。不用整个附件序列化充当快照，避免暴露额外字段。版本能力失败应与“合法但未开窍”区分。

验收：相同玩家同 tick 快照一致；快照读取前后 PersistentData、附件、scoreboard 条目数均不变；NaN/Infinity/超长字符串返回空；缺 objective 不创建 objective；另一个玩家 UUID 不串入。不得在 adapter 调用 markSyncDirty。

### FactionJournalModule.java — evaluate

签名 `public Optional<ModuleDecision> evaluate(CoreSnapshot snapshot,ChronicleState state)`。两个参数非空且同 UUID，snapshot.opened=false 时无变化。非法输入抛 IllegalArgumentException；无变化返回空。返回状态只改 faction，不改其他模块、revision 或总 runId。

标记：去重记录势力身份组合并生成宗门见闻条目，最多保留 128 个组合且不修改本体头衔。

验收：首次 opened 快照收录当前组合；重复组合不二次生成 entries；`["a|b","c"]` 与 `["a","b|c"]` 不碰撞；满 128 后只更新最后观测值，不扩容/挤出旧条目。runId 变化保留组合集合，无额外奖励。相同 tick 重入得到同一候选，不产生随机 ID。

### MeritArchiveModule.java — evaluate

签名与上同，参数/异常/返回约定同抽象类；仅改 merit。opened=false 时无变化。

标记：建立贡献基线并在后续观测峰值跨越数据表门槛时解锁档案，消费下降不产生奖励。

首次 lastObservedTick=-1 或 snapshot.runId != state.runId，只把 last/peak 设置当前值，保留已解锁集合，不补发；之后以 max(旧峰值,当前值) 观察跨越。贡献下降不重置峰值、不增加条目、不把差分累积成可花余额。真实本体会钳到 0..80；不在本模块写回钳制。快照出现越界正值可原样观测，但不可据此推导任务完成。

验收：首次贡献 80 不补发；首基线 0→10 只得 merit_first；10→40 解锁 merit_record；40→80 解锁 merit_legacy；80→0→80 不再生成 entries；新 runId 80 不补发；跨多个阈值按表序输出，重复采样不重复提交。消费前后短暂峰值不可见是允许限制。

### ReputationJournalModule.java — evaluate

签名与上同；仅改 reputation。opened=false 时无变化。首次/新世代只建基线，后续正向峰值跨表阈值产生条目，集合跨世保留。

标记：按声望峰值生成一次性纪事条目，转世重建基线并保留已解锁纪事。

验收：首次 -100 留存负值；-100→100 解锁 reputation_known；100→1000 解锁 reputation_renowned；1000→5000 解锁 reputation_legend；5000→-100→5000 不重复；已有条目跨转世保留。不得把 mingsheng 改成非负数，也不得改 KE1 生成的 renqi。

### NbtChronicleRepository.java — load / save / copyForClone

`public Optional<ChronicleState> load(ServerPlayer player)`：缺根返回空；未来 schema、错误类型、缺关键键、非法集合、UUID 不符抛 IllegalStateException，原数据保留，不自动归零。服务端主线程；返回深度不可变数据。

标记：解码并验证独立 NBT 根及 schema，保留损坏数据并区分缺失与错误。

`public boolean save(ServerPlayer player,long expectedRevision,ChronicleState next)`：expected=-1 代表根不存在；next.revision=expected+1，next UUID 必须匹配 player，schema 必须为 1。参数不合法抛 IllegalArgumentException；线程或原存档损坏抛 IllegalStateException；版本冲突返回 false、不覆盖。完成编码与校验后一次 put 独立根，不操作其他根。不得将 false 当成功播报。

标记：校验所有者和 revision 后原子保存 daotu_chronicle，禁止写入旧道途及天命根。

`public void copyForClone(ServerPlayer original,ServerPlayer replacement)`：同 UUID、服务端主线程。缺原根不创建目标；有原根时深拷贝，目标已有更高有效 revision 不覆盖。UUID 不同抛 IllegalArgumentException；原/目标损坏或线程错抛 IllegalStateException。不能用“复制整个 PersistentData”代替。

标记：在玩家克隆生命周期深拷贝独立根，避免共享标签及旧实体覆盖新版本。

建议存储映射：根内 playerId UUID、schema int、revision long、runId int；faction/merit/reputation 为 compound；记录字段与 POJO 同名；集合为 string list。编码细节由 Agent B 完成，但不能改公共类型；每项严格校验 NBT 类型，不能让 getDouble 缺键返回 0 掩盖坏档。

验收：空档 load 无写入；正常 roundtrip；schema=2 不覆盖；缺任一关键键不覆盖；128→129 项拒绝；save(-1,state.rev=0) 首次成功、第二次 false；过期 revision 提交 false；Clone 后修改原标签不影响新标签；其他根字节不变；重登数据一致。无需引入 SQLite/YAML 依赖。

### ChronicleCoordinator.java — observe / show

`public void observe(ServerPlayer player)`：只在服务端主线程。适配器返回空直接暂停，不创建默认存档；未开窍不评估。缺自有存档时建立 schema=1/rev=0 的初始状态（各 lastObservedTick=-1），使用完整快照建基线。按装配顺序评估，每次将已合并的工作状态传给下一个模块，但总 runId 保留旧值直到最后，以便三个模块都能识别换世代。模块不能改其他子状态；校验通过后设置总 runId 和单次新 revision，save 一次。无实际状态变化不 save。

标记：校验门禁并读取快照，顺序合并模块结果，以单次 revision 提交且拒绝部分更新。

模块异常/坏档中断整批；不提交前半批，不循环重试刷 tick。版本冲突跳过并下一次重新读取；不可把原候选套用到新版。首次缺档 expected=-1，已有档 expected=旧 revision。新条目只能在成功提交后播报；同一采样不得逐模块多次保存。

`public int show(CommandSourceStack source)`：只读展示当前玩家三个档案；控制台、不可用、无档时解释原因并返回 0；成功返回 1。不创建存档、不调用 observe 补奖励、不打开屏幕、不查别人的数据。输入非空；程序错误可抛 IllegalArgumentException，业务不可用用可理解反馈。无自定义异常类型。

标记：为当前玩家展示三模块纪事及不可用原因，控制台失败返回 0。

验收：三模块同次变化仅一次 save；中间模块抛错零次 save；空适配器零 load/save；重复 tick 无条目重播；控制台执行返回 0 且不抛未处理的玩家类型异常；两个玩家互不影响。构造器只做依赖装配，不读取世界。

### ChronicleEvents.java — onLogin / onTick / onClone

`public void onLogin(PlayerEvent.PlayerLoggedInEvent event)`：过滤服务端玩家后分发 observe；仅首次档案建基线，不调用旧登录迁移；任何可恢复失败限频记录，不能在客户端写存档。

标记：服务端玩家登录时请求协调器采样建立基线。

`public void onTick(PlayerTickEvent.Post event)`：服务端玩家、每 20 tick 一次；允许和登录在同 tick 触发，但协调器应幂等。无全局 static 玩家状态、不为每玩家开线程、不逐 tick 反射扫描本体类。

标记：过滤服务端玩家并按 20 tick 节流调用协调器。

`public void onClone(PlayerEvent.Clone event)`：确认 original/replacement 都是同 UUID 服务端玩家后调用仓储 Clone，普通死亡不重置独立历史。不判断 zhuanshu 来推断转世；下一次快照用 runId 变更换基线。若附件访问生命周期需要额外操作，必须先核对 249 API，并加入证据，不能猜 reviveCaps 等旧 API。

标记：校验服务端同 UUID 玩家后调用仓储克隆，下一次采样识别 runId 切换。

事件方法不向总线泄漏预期存档/适配失败；记录上下文后暂停该玩家新模块，不能修改其他附属。验收：客户端事件零业务调用；20 tick 内最多一次周期采样；Clone 同 UUID 深拷贝，普通死亡历史仍在；转世只重建基线，不丢历史。

## 5. 目标时代构建命令与超时

PowerShell 下使用可用 Python（本机 PATH 无 python）：

```powershell
$py = 'C:/Users/ADMIN/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$env:PYTHONIOENCODING = 'utf-8'
& $py _crash3/javac_check.py
# 只有上一条退出 0 才继续
& $py _crash3/pack_jar.py
& $py _crash3/verify_architecture.py
```

编译建议超时 180 秒；打包 60 秒；完整复用探针 `_crash3/audit_1020.py` 建议 600 秒。当前编译一般数秒，首次读取本地 jar 可较慢。缺 Java 或依赖应报错停止，不降级平台、不伪造占位依赖。不要跑 gradlew/Gradle，不执行 bump_version.py、bump_toml.py；没有 wrapper。

verify_architecture.py 执行静态检查及读取打包结果，不替代前两条命令。它要求保持当前骨架的 12 个标记，适用于架构交付；Agent B 填实现后应同步其阶段预期（待填总数应降至 0）并新增行为验证，不能为了通过去保留假占位。

本地 JDK21 的 `--release 21` 实测在编译器资源关闭阶段失败，改用同一 JDK21 的 `-source 21 -target 21` 后退出 0；此编译路径不使用更高版本 JDK。离线工具辅助库取自 1.21.1/263 安装清单，NeoForge 核心三项明确为 249 平台 jar 与对应 MC jar，未把主版本替换为 263。

打包仍为 `build/libs/daotu-1.5.2.jar`，可能覆盖同名本地输出；不安装到游戏目录，不发布，旧版本号不变。工程保留原元数据；不要新增 fabric.mod.json 或 plugin.yml。

## 6. UNVERIFIED

- U1：精确 21.1.249 的完整传递依赖清单及运行验证未取得；编译用 249 平台 jar 与现有 1.21.1/263 辅助清单，不能把编译通过当专服启动通过。
- U2：Gradle 9.2.1 + ModDevGradle 2.0.144 的联合路线未运行，用户明确禁止；坐标已锁定，插件版本官方条目存在，无本体发布 Maven 坐标可确认，因此用指定本地 jar。
- U3：仅靠现有 probe_persist 不能证实 Player PersistentData 自动复制；Clone 深拷贝待实机验收。
- U4：所有其他附属、脚本和反射路径对本体字段的写入不可穷尽，尤其 shenfen 已被旧道途占用，禁止接管。
- U5：require=0 mixin 是否在实际整合包成功注入、与天命 HEAD 顺序是否影响账本未测；不新增 mixin 降低这一阶段风险。
- U6：没有不同字节的旧本体对照，不能声称发现版本间语义变更；只能说明现有注释/假设与 10.20 实测不符。
- U7：只读 scoreboard 分数查询的具体 1.21.1 方法签名、Clone 附件生命周期 API 在待填业务中尚未使用，Agent B 必须先 javap 核对，不能凭空写 API。架构的原生事件及命令注册 API 已由 249 编译确认。
- U8：纪念条目的展示体验、采样错过短暂峰值、多玩家压力与存档损坏反馈尚未游戏内验证；目前骨架方法不提供功能。

## 7. 完成判据

架构阶段：45 个 Java 源文件编译退出 0；pack_jar.py 退出 0；jar 含 12 个新顶层类及 record 嵌套类；新源码无 BOM；既有 33 文件的方法签名不变，只有主类增加装配；版本文件与元数据不改；恰好 12 个规范标记且已逐一列契约；verification.json 中检查通过。

编码阶段：12 标记均填完并更新规范与验证预期；对三个纯模块和仓储/协调器完成上述有意义的行为验证；重新 javac/pack 退出 0；检查客户端与专服启动、两个 mixin 实际加载、双玩家隔离、重登、普通死亡、寿尽转世、同装天命；仅触发新纪事时本体及其他附属字段不变；不改变现有公开接口和旧网络协议。任何未验证项继续列 UNVERIFIED，不写“全兼容”。
