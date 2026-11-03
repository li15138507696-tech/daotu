# 道途 × 本体 9.8 深层适配报告

> 2026-11-01

对象：`daotu-1.8.0.jar` → 适配到 `guzhenren蛊真人模组本体9.8.jar`（扁平 jar，106 608 442 bytes，22 582 class，699 实体）。

## 结论先说

**道途 1.8.0 对 9.8 已经二进制完全兼容，不需要为兼容性改任何代码。**

我把六层都核过（下面逐条列证据），并在真专用服务端上跑通了。
本轮唯一的代码改动是**把「本体版本」这件事从文档搬进代码**（见第三节），
因为原来 `Core1020Adapter` 被无条件实例化、名字和文档却写着「仅适配 10.20」，
这个边界在代码里是隐形的。

---

## 一、逐层核对

### 1. 类引用

道途字节码里引用的本体类只有 6 个，**9.8 全部存在**：

```
net.guzhenren.init.GuzhenrenModGameRules
net.guzhenren.init.GuzhenrenModMobEffects
net.guzhenren.network.GuzhenrenModVariables
net.guzhenren.network.GuzhenrenModVariables$PlayerVariables
net.guzhenren.procedures.JingJieBaoCunProcedure
net.guzhenren.procedures.UikongqiaoquedingProcedure
```

### 2. PlayerVariables 字段

道途用到 67 个字段（`daohen_*` / `dahen_*` / `liupai_*` / `shili` / `shenfen` /
`GongXianZhi` / `mingsheng` / `qiyun` / `kongqiao` …）。

**9.8 与 10.20 的 `PlayerVariables` 都是 411 个字段，集合完全相同。**

包括那几个 10.x 库层才「看起来该有」的：

```
public java.lang.String shili;
public java.lang.String shenfen;
public double GongXianZhi;
public double mingsheng;
```

方法集也一致（6 个），含道途每次写字段都调的 `public void markSyncDirty();`。

### 3. Mixin 目标

| Mixin | 目标 | 9.8 | 10.20 |
|---|---|---|---|
| `JingJieBaoCunProcedureMixin` | `JingJieBaoCunProcedure.execute(Event, LevelAccessor, Entity)` | 存在 | 存在 |
| `UikongqiaoquedingProcedureMixin` | `UikongqiaoquedingProcedure.execute(LevelAccessor, Entity)` | 存在 | 存在 |

注意 `JingJieBaoCunProcedure` **两个版本都有两个 `execute` 重载**：
`public (LevelAccessor, Entity)` 和 `private (Event, LevelAccessor, Entity)`。
道途注入的是后者，两版都在，签名一致。

### 4. 静态成员

| 成员 | 9.8 | 10.20 |
|---|---|---|
| `GuzhenrenModGameRules.XIUWEI` | 有 | 有 |
| `GuzhenrenModMobEffects.FUHUO` | 有 | 有 |

### 5. 流派 buff（12 个白名单）

`DaotuBuffs` 通过 `BuiltInRegistries.MOB_EFFECT.getHolder(...).orElse(null)` 取，
**缺失不会崩、只会静默无效果**——所以必须逐个验。结果：

```
shuidaozengfu / yudaoguchongweilizengfu / qidaoguchongweilizengfu /
jiandaoshanghaizengfu / lvdaozengfu / jindaozengfu / yandaozengfu /
leidaozengshang / weilizengjia / daligubuff / tiexue / leishen
```

**12 个在 9.8 与 10.20 里全部存在**（两版 `GuzhenrenModMobEffects` 都抽出 349 个效果名）。

### 6. 注册表 id

道途引用的 `guzhenren:` 命名空间 id 数量为 **0**——它不碰任何本体实体/物品/方块注册名，
只走 `PlayerVariables` + scoreboard + 效果。所以 9.8 与 10.x 的实体增删（699 vs 656）
对道途没有影响。

---

## 二、真服务端验证

### 9.8 需要外部依赖（这点 10.20 不一样）

10.20 是 jar-in-jar 包装，GeckoLib 等内嵌；**9.8 是扁平 jar，依赖要外挂**。
第一次直接启动直接崩：

```
Failed to create mod instance. ModID: guzhenren, class net.guzhenren.GuzhenrenMod
java.lang.NoClassDefFoundError: software/bernie/geckolib/animatable/GeoBlockEntity
```

补齐后正常：`geckolib` / `pehkui` / `attributefix` / `bookshelf` /
`player-animation-lib` / `prickle`（+ `curios`、`patchouli` 备用）。

### 启动结果

```
[10:21:20] [Server thread/INFO] [minecraft/DedicatedServer]: Done (1.857s)!
[10:21:21] [daotu/]: [道途] 本体版本 9.8（独立扁平 jar；实体 699 个，含毛僵/跳僵，无 gu_xiu）；本次会话按该版本的能力集运行
ERROR 总数 4，道途相关 0
```

4 条报错全是本体自身数据问题（`guzhenren:fangju` 标签、`nilvhuafenjie` 配方、
`zijingsheligu` 成就、`deleted_mod_element`），与道途无关。

### 命令与实体

| 用例 | 9.8 结果 |
|---|---|
| `/daotu-chronicle` | `[道途·纪事] 该命令只能由玩家执行`（命令已注册，按设计拦玩家判定）|
| `/gzlib status` | 正常（库前置）|
| `/summon guzhenren:dian_lang` | `Summoned new 电狼` |
| `/summon guzhenren:jiang_shi_gu_xiu` | `Summoned new 毛僵` ← **9.8 独有**，证明版本判定真实 |
| `/gjl`、`/daohen` | **9.8 里不存在**（10.20 有）← 本体自身的命令差异，道途不用它们 |

---

## 三、本轮的代码改动（v1.8.1）

只加了一件事：**把本体版本显式化**。

1. 新增 `DaotuCoreVersion`（枚举 + 内容指纹检测）
   - `jiang_shi_gu_xiu` 实体 → **9.8**
   - `com.guzhenrenlibrary.faction.FactionNpcManager` 类 → **10.20**
   - `gu_xiu` 实体 → **10.4**
   - 都不匹配 → 未知

   检测结果缓存，但**只缓存确定结论**：`EntityType` 注册表在类加载早期可能没填完，
   那时两个 `hasEntity` 都会 false；如果连 `UNKNOWN` 一起缓存，会把「暂时查不到」
   永久钉成「未知版本」。所以 `UNKNOWN` 每次重算。

2. `DaotuEvents` 新增 `ServerStartedEvent` 处理器，服务端就绪后打一行版本日志
   （放这里而不是构造器，同样是为了等注册表填好）。

3. `Core1020Adapter` 的类文档改成「已验证 9.8 / 10.4 / 10.20」，
   并写明 9.8 上的语义差别（见下）。

### 9.8 与 10.x 的语义差别（不是错误，但要知道）

- 9.8 **没有库层的势力系统**，`shili` 字段存在但不会被本体写入 →
  **宗门见闻簿恒为空**。`shenfen`（头衔）仍由道途自己写，正常显示。
- 9.8 实体 699 个（含毛僵/跳僵），10.x 656 个（含 `gu_xiu`）。

---

## 四、验证

| 项 | 结果 |
|---|---|
| `javac_check.py` | `sources: 47` / `javac exit: 0` |
| `pack_jar.py` | `daotu-1.8.1.jar` 129 977 bytes |
| 9.8 专用服务端 | `Done (1.857s)`，道途相关 ERROR **0**，日志正确报 **9.8** |
| 10.20 专用服务端（交叉验证） | `Done (2.073s)`，日志正确报 **10.20** |
| mixin 配置 | 2 个 mixin 完整，`required: true`，priority 1100 |
| 文本资源 BOM | 无 |

---

## 五、我这轮自己犯的四个错（都不是 mod 的问题）

记录下来，因为每一个都一度让我得出错误结论：

1. **字段审计假阴性**：正则只写了 `String`，而实际声明是 `public java.lang.String shili;`
   → 误报「`shenfen`/`shili` 在 9.8 缺失，会 `NoSuchFieldError`」。用宽匹配后两版都是
   **411 个字段且完全一致**。
2. **mixin 签名误判**：把天命的 mixin 目标（`Xiulianjingjie…` / `UIxiuliananjian`，五参）
   当成了道途的目标，误报「9.8 签名不匹配」。实际道途目标的两参/三参重载两版都有。
3. **PowerShell 吃掉 `$PlayerVariables`**：内联 `python -c` 里类名被变量展开，
   于是查的是外层类，误报 `markSyncDirty` 不存在。改成写文件后正常。
4. **类引用过滤前缀写错**：`net.guzhenren/`（点+斜杠）与过滤器 `net/guzhenren/`（全斜杠）
   不一致，把道途自己的 61 个类算成了「缺失的本体类」。

---

## 六、待你确认

`daotu-1.8.1.jar` 已经构建并在我这边的 9.8 测试服上验证通过，
但**你的整合包 mods 目录里目前没有道途**（只有本体 9.8 + 库前置 + fushu + maid）。

要我把它装进 `D:\game\mcmod\1\.minecraft\versions\转生到蛊界就要拿出真本事\mods` 吗？
另外提醒：9.8 是扁平 jar，如果你还要装**天命 / 恶意**，它们同样需要
GeckoLib 等外挂依赖（10.20 那套是内嵌的，不能直接照搬）。
