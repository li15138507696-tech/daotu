<!-- Path: PLAN.md -->
# 道途 1.5.2 × 本体 10.20：适配审计与新玩法架构

1. 平台固定 NeoForge 21.1.249、Minecraft 1.21.1、Java 21；版本仍为 1.5.2。
2. 外壳内层 jar、指定抽取文件、旧编译依赖的 SHA-256 一致；没有证据支持二者间存在 ABI 或语义迁移。
3. 审计基线实际为 33 个 Java 文件、5516 行、411 个 public 字段；不沿用请求中的旧计数。
4. 新增宗门见闻簿、功绩档案、声望纪事三个独立模块；本体数据全部只读。
5. 交付可编译的空骨架、数据表及 FILL-SPEC；玩法、存档及事件处理由 Agent B 填充。

## 证据与审计边界

根目录 `D:\daima\mcmod\道途附属`。2026-10-25 对以下三份内容计算 SHA-256，均为：

`b6d314d3810b8bc5fcfdbc4f588db8721f0efdfc14d27a0a06d88143a01fe2bc`

- `D:\cxdownload\guzhenrn蛊真人模组本体10.20.jar` 内 `META-INF/jarjar/guzhenren-0.1-neoforge-1.21.1.jar`。
- `D:\daima\mcmod\蛊真人附属\_tmp_verify\guzhenren-core.jar`。
- 原编译依赖 `_reverse\nested\guzhenren-0.1-neoforge-1.21.1.jar`。

参考 `player-variables-fields.txt` 实际是 UTF-16，解析得到 411 个 public 字段，与本次 javap 名单完全一致，新增/删除均为空。源码实际行数包含注释和空行。本次不推测“410/4475”旧计数的原因。

沿用 `_crash3/probe_*.py` 的输出约定：`===` 段标题、常量池筛候选、`javap -p -c` 指令窗口、无法确认时显式标记。新增 `audit_1020.py` 只是补充全项目索引和证据归档；复用 `probe_qiyun/probe_persist/probe_kaiqiao/probe_zhuanshu` 的原脚本主体，执行时替换输入 jar，不覆盖原探针。已阅读 `probe_main_liupai/probe_growth_runtime/probe_zhuanshu_range/audit_main_dao` 的约定；其旧缓存不能作为 10.20 的独立证据，故重新 javap。`audit_jar.py` 仍引用已删除旧类，不作为本次通过依据。

证据目录 `_crash3/audit_1020/`：

- `source-snapshot.txt`：改动前全部 33 个源文件的完整快照。
- `inventory.json`：逐文件、逐行本体引用索引；无引用文件也列入，不只检查 import。
- `PlayerVariables.javap.txt`：完整字段、方法及描述符。
- `hooks.javap.txt`：103 个相关候选类及直接依赖、开窍/转世/效果钩子的完整反汇编。
- `reused-probes.txt`：原探针执行结果。`probe_persist` 未找到 `Player.copyFrom`，不能据此证明复制可靠。
- `verification.json`、`compile.log`、`pack.log`：最终静态检查、编译及打包实跑证据。

常量池筛选用于确定反汇编候选，不等价于证明读写；结论取自 getfield/putfield、调用描述符及分支。反射、外部脚本、其他附属未来写入不在封闭世界证明范围内。

## 适配缺口：已失效

**本次未发现直接字段/类/执行方法的 ABI 失效或改签名。** 原 jar 与新 jar 字节一致，既有方法签名不能称为“升级后变化”。全部 33 源文件在新固定 classpath 下编译；反射之外的字段和静态注册成员受编译校验。两个 mixin 的目标类及 execute 描述符均存在，运行时注入是否成功另行验收。

已失效的是这些旧描述及工程假设：

- `neoforge.mods.toml` 描述仍宣传十六出身、六档势力、六大道统；对应玩法已撤除，不代表 1.5.2 的运行行为。本轮按要求保留该文件及版本，不擅自改产品描述。
- `DaotuRuntime` 类注释的“按贡献刷新势力档位”在方法体已不存在。
- `DaotuMod` 声称与天命写字段完全不重叠，和 `DaotuGrowthApply`、`DaotuSpecial`、`DaotuTalentApply` 的实际写入矛盾；这是最高风险，不能宣称整个现有道途已与天命无冲突。
- 编译器原先按库数量选择 21.1.263，违背本次矩阵；现固定平台 jar 为 21.1.249、MC 1.21.1，并检查指定内层 jar 必须存在。其他依赖来自现有 21.1.263 的 1.21.1 清单，来源明确但不是精确 249 运行环境证明。

## 适配缺口：语义改变／需要纠正的理解

这里区分“旧注释或候选假设不符”与“两个 jar 间发生变化”。前者如下，后者因 SHA 一致未检出。

- `shili:String` 不是无人写入：`ShengZhuanDangYouJiKongQiShiShiTiDeWeiZhiProcedure.execute(Entity)` 偏移 141 加载“古月山寨”，144 写 shili，随后同步。不能用于附属势力独占存储。
- `shenfen:String` 在本体候选中仅见默认值、序列化、反序列化、克隆及 `UishenfenProcedure.execute(Entity):String` 展示；本体未发现玩法写入，但**旧道途 refreshTitles 已写它**。不能再让新模块覆写该字段。
- `GongXianZhi:double` 并非“有人写没人看”：`FengYuLouRenWuJiangLiProcedure`、`Rw19/21/22/26…` 奖励写入；`FengYuLou3`、`PaiMaiHangDuiHuan1`、`PaiMaiHangJingJia`、`RuChengLingShuXingZhiTiGongQi` 等读取。`KE1.execute(LevelAccessor,double,double,double,Entity)` 在 274–345 将贡献钳至 0..80；不能建累计余额、不能把差分称为完成任务。
- `mingsheng:double` 已参与 `KE1` 的 renqi 计算（6751 起），`UishengwangProcedure` 展示；上述 ShengZhuan procedure 可增加或减少，不能当作闲置荣誉槽。
- `mingge` 被天资、突破、修炼等多条流程使用。新模块不写、不借用它；不根据名称推导枚举。
- `qiyun_shangxian` 会被 `Qiyunshuzhi/Sx/Tianziliucheng/Uikongqiaoguanbi` 写入，不能声称本体“从不覆盖”。`KE1` 在 2006–2056 比较上限与当前值并写当前气运，旧 `DaotuRuntime` 与 `DaotuSpecial` 的文字描述存在相反比较方向，必须按指令分支验收，不借此拓展新模块。
- `zhuanshu` 是本体境界值，`JingJieBaoCun` 可重置为 0，不是每次转世自增的世代号。世代必须只读道途 `daotu/run/id`；升境界不等于新一世。
- `DaotuDraw.capOf(double)` 实际以 `< 5.0` 为界，因此五转已经无限；与“一至五转均 100”的注释不符。只记录，未改业务。
- `SiqibuffXiaoGuoChiXuShiMeiKeFaShengProcedure` 的清除效果调用仍存在；一次性发 buff 不可靠。新模块不发 buff。
- `Player.copyFrom` 探针无结果，不能沿用“PersistentData 默认必复制”作为设计基础。新仓储显式定义 Clone 深拷贝。

## 新增可用钩子（对道途尚未接入，并非宣称 10.20 才新增 API）

- `UiShiliProcedure.execute(Entity):String`、`UishenfenProcedure.execute(Entity):String`：本体展示消费端；新玩法观察其底层同名字段，不调用 setter，也不重新定义本体身份。
- `FengYuLouRenWuJiangLiProcedure.execute(Entity):void`：贡献的实际来源证据；方法含奖励副作用，**禁止新模块主动调用**。默认采用每秒快照，接受丢失短暂峰值；若将来需要精确任务完成事件，须另审该 procedure 的成功分支后再设计注入。
- `UishengwangProcedure.execute(Entity):String`：声望展示钩子；与 shenfen 相同，展示程序的存在不表示字段空闲。
- `UikongqiaoquedingProcedure.execute(LevelAccessor,Entity)` 偏移 7 调 `UikongqiaoguanbiProcedure.execute(LevelAccessor,Entity)`；现有 TAIL 仍是候选开窍收尾，但本轮不添加第三方顺序依赖。
- `JingJieBaoCunProcedure` 的私有 `execute(Event,LevelAccessor,Entity):void` 描述符存在。FUHUO、XIUWEI 与 shouyuan 分支仍能找到；现有 HEAD 拦截不改。新玩法从已提交的 runId 变化识别转世。
- 原生 `PlayerLoggedInEvent`、`PlayerTickEvent.Post`、`PlayerEvent.Clone` 与 `RegisterCommandsEvent` 已由 249 jar/既有代码和最终编译核对；新事件体保持空壳。

## 逐文件审计结论（原有 33 文件）

具体行号以 `inventory.json` 与源码基线为准；下列包含直接和传递依赖。

| 文件（net/guzhenren/daotu 下） | 本体耦合与结论 |
| --- | --- |
| DaotuApply.java | 44 个道痕原始字段只读，含 9 个 dahen 拼写；均存在且 double。 |
| DaotuAttributes.java | 间接调用 RunAttributes，无本体成员引用；现有签名保留。 |
| DaotuBuffs.java | 12 个 guzhenren 效果字符串均在 ModMobEffects 注册字面量中；不能只凭语言文件认定注册存在。 |
| DaotuCombatEffects.java | zhenyuan/zuida_zhenyuan/niantou/niantou_rongliang 均存在；当前量回复会与其他附属相加，新增模块禁止复用奖励路径。 |
| DaotuData.java | 只用自有 daotu NBT 根；wipeAll 删除整个根，新模块用独立兄弟根以免误删。 |
| DaotuDraw.java | 传递触达 Special/TalentApply；五转门槛与注释不符、转数不是世代。 |
| DaotuDrawTable.java | 通过 Run.zhuanshu 与候选表消费境界；不直接调用本体 procedure。 |
| DaotuEvents.java | 原生事件→旧道途服务，无直接本体字段；不改变事件业务体。 |
| DaotuGrowthApply.java | 写 shenfen、44 道痕及 15 流派字段，均存在；与天命禁写集合有实际重叠。 |
| DaotuLiLian.java | 通过 Run 读境界、通过 Opening 读 kaiqiao；原版实体/群系注册键，无硬编码本体实体类。 |
| DaotuMainDao.java | 15 条可选主修，两侧字段均存在；“16 条”旧注释有误；不等价于本体官方主修字段。 |
| DaotuMigrate.java | 迁移自有数据，间接触发发奖与 shenfen 更新；不用于新模块首次建档。 |
| DaotuMod.java | 注册旧事件和 5 个协议 3 的 payload；本轮只增加独立事件、命令与依赖装配。 |
| DaotuNet.java | 将 Run 的本体境界结果封入旧状态包；本轮不改既有网络签名及协议。 |
| DaotuOpening.java | PLAYER_VARIABLES/shouyuan 等转世依赖及 kaiqiao 记分项；当前 hasOpenedQiao 的 getOrCreate 会创建分数，新适配器不复用该有副作用读法。 |
| DaotuRun.java | 直接取 PLAYER_VARIABLES.zhuanshu:D；runId 是自有 id，必须与境界分开。 |
| DaotuRunAttributes.java | 14 个原版 Attribute，modifier ID 是 daotu:run_*；没有占用本体 registry namespace。 |
| DaotuRuntime.java | 读写 qiyun_shangxian、markSyncDirty；当前 pct=0 使其加成分支不执行；注释不符。 |
| DaotuSpecial.java | 15 主修道痕/流派与 qiyun_shangxian 奖励；动态构造字段键均核对，禁止新模块调用。 |
| DaotuTalent.java | 纯数据表，DAOHEN 参数由 TalentApply 落地；不是本体新 registry。 |
| DaotuTalentApply.java | 直接写道痕并同步，buff 经 DaotuBuffs 注册键消费；与天命共享字段风险。 |
| client/DaotuClientEvents.java | 原生客户端键盘/事件，没有本体字段/registry/procedure 依赖。 |
| client/DaotuClientHandler.java | 只消费自有 payload，无本体写操作。 |
| client/DaotuClientPrefs.java | 客户端偏好文件，无本体 API。 |
| client/DaotuKeyMappings.java | 自有键位注册，无本体 API。 |
| client/DaotuViewScreen.java | 消费旧状态包及自有主修/候选表，无直接本体可变附件；不将它挂入新模块。 |
| mixin/JingJieBaoCunProcedureMixin.java | 目标私有 execute 描述符存在；FUHUO、XIUWEI、shouyuan:D 均存在，运行注入仍需联机验收。 |
| mixin/UikongqiaoquedingProcedureMixin.java | execute(LevelAccessor,Entity):void 存在，转调 guanbi 证据保留；require=0 不保证实际注入。 |
| net/DaotuMainDaoPayload.java | 旧协议接受主修键、间接影响奖励字段选择；白名单原样保留。 |
| net/DaotuPickPayload.java | 选择下标经旧服务传递至发奖，无直接本体符号；本轮不扩展。 |
| net/DaotuRequestPayload.java | Opening 的 kaiqiao 门禁；不给新纪事添加强制弹窗。 |
| net/DaotuSettingPayload.java | 只写旧道途 autoPrompt，无本体成员。 |
| net/DaotuStatePayload.java | 记录型旧协议，含只读 zhuanshu；本轮保持签名与字段顺序。 |

全部效果键：shuidaozengfu、yudaoguchongweilizengfu、qidaoguchongweilizengfu、jiandaoshanghaizengfu、lvdaozengfu、jindaozengfu、yandaozengfu、leidaozengshang、weilizengjia、daligubuff、tiexue、leishen。FUHUO 为 DeferredHolder；XIUWEI 为 GameRules.Key；PLAYER_VARIABLES 为 Supplier；markSyncDirty 描述符 `()V`。新模块不增加物品、实体、配方注册。

## 架构与目录

```text
PLAN.md / FILL-SPEC.md
build.gradle / settings.gradle / gradle.properties   锁定矩阵的声明，禁止在本任务运行 Gradle
src/main/java/net/guzhenren/daotu/
  DaotuMod.java                                    保留原构造及注册，增加新组合根
  chronicle/
    ChronicleModels.java                          不可变数据记录与 schema/root 常量
    ChronicleTables.java                          三模块的设计数据
    CoreVersionAdapter.java / Core1020Adapter.java 本体只读版本边界
    ChronicleModule.java                          纯计算模块抽象契约
    FactionJournalModule.java                      宗门见闻簿
    MeritArchiveModule.java                        功绩档案
    ReputationJournalModule.java                   声望纪事
    ChronicleRepository.java / NbtChronicleRepository.java  仓储边界与空壳
    ChronicleCoordinator.java                      串行事务编排与查询入口空壳
    ChronicleEvents.java                           登录/tick/Clone 空监听器
_crash3/audit_1020.py / verify_architecture.py       证据与工程验证工具，不是玩法实现
```

唯一依赖方向：事件/命令 → 协调器 → 只读适配器 + 三个纯模块 + 仓储。模块之间不互调、不持有 ServerPlayer；版本变化只替换适配器，不给现有 PlayerVariables 添字段。此轮只支持已审计的一个本体构建，不宣称跨版本可运行。

主类已完成事件及 Brigadier 命令 `/daotu-chronicle` 注册，命令当前返回 0。NeoForge 不存在 Bukkit 的 TabCompleter 注册约定：无参数 literal 由 Brigadier 提供补全；不生成 plugin.yml 或 fabric.mod.json。元数据沿用现有 neoforge.mods.toml，文件及版本号均保持；不虚构平台依赖。

## 三个玩法模块

### 宗门见闻簿

利用本体缺少玩法写入的 shenfen 展示槽及 shili 展示 procedure，将玩家经历过的“势力、身份”组合收集为见闻，而不是再次抢占本体头衔。首次登录及每 20 tick 服务端采样，只有开窍才记录；不同的组合收集一次，最多 128 项，满后不覆盖历史，只更新最后观测值。字符串按原值处理、限制各 128 个 Unicode 码点，组合键用 JSON 数组或长度前缀避免分隔符歧义，不推测阵营 ID。

模型 `FactionJournal(discoveredPairs,lastFaction,lastIdentity,lastObservedTick)`。输入只读 `shili/shenfen`，输出仅 `daotu_chronicle/faction`。已收集见闻跨世保留；“本体未使用”的严格结论只限 shenfen 无玩法写入，旧道途仍是该字段写方。新模块不改 shenfen，不参与抽选称号计算，不调用 UiShili/Uishenfen 的其他副作用路径。

### 功绩档案

将已被本体使用但旧道途没有消费的贡献观察结果整理为“初积功绩、功绩成册、功绩留名”三项档案。设计阈值 10/40/80 受已证实的 80 上限约束，不宣称来自本体设计。首次或新世代仅记录基线；后续峰值首次跨过阈值，保存一条一次性纪念条目。

模型 `MeritArchive(lastObserved,peakObserved,unlockedEntries,lastObservedTick)`。只读 `GongXianZhi`；不累计差分、不扣贡献、不判定具体任务、不发本体物品/属性。下降只更新 lastObserved，旧峰值不下降；转世重建峰值与基线，条目跨世保留。不能捕获两次采样之间被钳平的奖励，属于有意设计限制，不通过调用奖励 procedure 补偿。

### 声望纪事

把声望与 NPC 面板之外尚未被道途消费的历史维度做成可收集纪事；阈值 100/1000/5000 是本附属的设计表。首次采样不补发历史；后续正向峰值跨越门槛后解锁一次。保留负声望原值，但不据此发奖或纠正本体数值。

模型 `ReputationJournal(lastObserved,peakObserved,unlockedEntries,lastObservedTick)`。只读 `mingsheng`；本体的 renqi 仍由 KE1 计算，不能改写。已解锁纪事跨世保留；新世代只换基线。该字段并非本体闲置字段，新增的是历史消费层，禁止把已有功能包装成“本体没人用”。

## 数据边界与生命周期

本体写集合为空；新模块也不写旧 `daotu`、`tianfu`、`tizhi`、`daohen_*`、`dahen_*`、`liupai_*`、`v2_*`，不调用旧发奖服务。独立根是 PersistentData 的 `daotu_chronicle`，不是 `daotu` 子项；旧 wipeAll 不会删它。自有状态字段详见 ChronicleModels，建议 NBT 层保持同名键。

`ChronicleState(playerId,schema,revision,runId,faction,merit,reputation)`：schema=1，初建 revision=0（expected=-1），正常每事务加一；各集合不可变。每个模块只改自己的记录，协调器顺序传递已合并状态，最后统一更新 runId/revision 并提交一次；异常时不写部分结果。仓储是线程内的版本比较，不是跨线程数据库事务。

runId 只读 `DaotuRun.runId`，其 getter 不创建标签；缺失视为 0。快照 gameTick 为服务端世界游戏时间；不拿 zhuanshu 判定世代。首次初始化各 lastObservedTick=-1 作为无基线标志；真正记录基线后写当前 tick。转世后的首次观测保留历史集合，重建本局基线。Clone 深拷贝根；不假设通用 PersistentData 自动继承。登录可采样；每秒 tick 兜底，不新增 procedure mixin，不改变双方开窍界面。

与天命并存的证明仅限新增模块的“空本体写集合、独立存储、无奖励回调、无自动弹窗”；既有道途写冲突不因此被修复。骨架没有新存档副作用，也没有真实玩法效果。

## 实施顺序与验证

- [ ] Agent B 先实现并验证只读适配器，错误时禁止创建纪事存档。
- [ ] 实现仓储的 schema/限长/所有者/版本检查与 Clone 深拷贝。
- [ ] 分别实现三个纯模块；覆盖首次基线、重复采样、消费下降、峰值跨越、新世代。
- [ ] 实现协调器单次提交，再填事件壳及命令展示；保持旧网络包与所有既有签名。
- [ ] 用下列离线工具重编译/打包，并在专服、同装天命环境验收；不能仅看 compile 成功就宣布 mixin 生效。

构建命令、每个占位位置与可操作验收在 FILL-SPEC。没有 wrapper，不运行 Gradle。build.gradle 只提供用户要求的矩阵声明；[ModDevGradle 官方用法](https://github.com/neoforged/ModDevGradle) 与 [2.0.144 插件条目](https://plugins.gradle.org/plugin/net.neoforged.moddev/2.0.144) 已查，未自行替换坐标。

## 风险与 UNVERIFIED

- **R1 最高**：现有道途已经写天命禁区道痕/流派。仅交架构不能在“不实现业务”的范围内修复它；Agent B 必须先设计现有奖励迁移/归属策略，禁止新增同类写入。
- **R2**：require=0 的 mixin 可能静默失效，HEAD 扣回道痕又与其他附属初始化顺序有关；专服实测尚未做。
- **U1**：精确 21.1.249 的附属库清单未取得；当前离线编译使用已安装 249 平台 jar + 1.21.1/263 清单的辅助依赖。主平台没有换成 263；完整运行时兼容性仍未验证。
- **U2**：Gradle 9.2.1 与 ModDevGradle 2.0.144 联合构建、开发运行及 Mixin 配置未实跑（用户禁止 Gradle）；两项锁定值原样保留，构建声明不等于 Gradle 路线通过。仅本体本地文件依赖，无臆造 Maven 坐标。
- **U3**：复制 PersistentData 在所有死亡/换维度/离线存档场景的保证未证实；probe_persist 返回 copyFrom not found。新仓储显式 Clone 方案仍待实现与实机验证。
- **U4**：跨 jar 的反射、脚本、其他附属对 shili/shenfen/贡献/声望的写入没有穷尽；不把本体静态扫描升级为全模组世界的独占保证。
- **U5**：采样错过短暂峰值是明确限制；是否需要精确任务事件须另立需求，当前不注入任务奖励过程。
- **U6**：无本体旧版（真正不同字节）的对照件，因此没有声称跨构建语义差异；本次参照实际是相同字节。
- **U7**：客户端展示、指令回执、持久化错误提示及多玩家隔离只定义契约，未做游戏内验证，空壳不当成可玩功能。

最终工具输出保存在 verification.json；没有执行安装、部署、版本递增或启动游戏。
