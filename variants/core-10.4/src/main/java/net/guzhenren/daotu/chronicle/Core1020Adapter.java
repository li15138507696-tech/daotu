// Path: src/main/java/net/guzhenren/daotu/chronicle/Core1020Adapter.java
package net.guzhenren.daotu.chronicle;

import java.util.Optional;
import net.guzhenren.daotu.DaotuOpening;
import net.guzhenren.daotu.DaotuRun;
import net.guzhenren.network.GuzhenrenModVariables;
import net.guzhenren.network.GuzhenrenModVariables.PlayerVariables;
import net.minecraft.server.level.ServerPlayer;
import net.guzhenren.daotu.chronicle.ChronicleModels.CoreSnapshot;

/**
 * 本体侧只读适配器。
 *
 * <p><b>已验证的版本</b>（2026-11-01 逐层核对，见 {@link net.guzhenren.daotu.DaotuCoreVersion}）：
 * <ul>
 *   <li><b>10.20</b> —— 原始审计对象；</li>
 *   <li><b>10.4</b> —— 与 10.20 是同一个内嵌 jar，字段完全一致；</li>
 *   <li><b>9.8</b> —— 扁平 jar，但 {@code PlayerVariables} 的 411 个字段与 10.x
 *       <b>完全相同</b>（含 {@code shili} / {@code shenfen} / {@code GongXianZhi} /
 *       {@code mingsheng}），所以同一套读取在这里同样安全。</li>
 * </ul>
 *
 * <p><b>9.8 上的语义差别</b>：9.8 没有库层的势力系统，{@code shili} 不会被本体写入，
 * 因此宗门见闻簿恒为空；{@code shenfen} 仍由道途自己写，正常显示。这不是错误，
 * 只是该版本没有势力概念。
 *
 * <p>只读四个本体字段（{@code shili} / {@code shenfen} / {@code GongXianZhi} / {@code mingsheng}）
 * 与开窍判定，<b>不写任何字段</b>，也不创建 scoreboard 分数。
 */
public final class Core1020Adapter implements CoreVersionAdapter {
    /** 与 {@link PlayerVariables} 实测字段名一一对应；改名即视为未适配。 */
    private static final String FACTION = "shili";
    private static final String IDENTITY = "shenfen";

    /** {@inheritDoc} 数值非有限或字段缺失时整单返回空，不返回部分快照。 */
    @Override
    public Optional<CoreSnapshot> read(ServerPlayer player) {
        if (player == null) {
            return Optional.empty();
        }
        if (player.getServer() == null || !player.getServer().isSameThread()) {
            throw new IllegalStateException("Core1020Adapter 必须在服务端主线程调用");
        }
        PlayerVariables v;
        try {
            v = player.getData(GuzhenrenModVariables.PLAYER_VARIABLES);
        } catch (RuntimeException e) {
            // 本体未安装或附件未挂载：视为版本不支持，不抛给上层。
            return Optional.empty();
        }
        if (v == null) {
            return Optional.empty();
        }
        double contribution = v.GongXianZhi;
        double reputation = v.mingsheng;
        if (!Double.isFinite(contribution) || !Double.isFinite(reputation)) {
            return Optional.empty();
        }
        String faction = v.shili == null ? "" : v.shili;
        String identity = v.shenfen == null ? "" : v.shenfen;
        return Optional.of(new CoreSnapshot(
                player.getUUID(),
                player.level().getGameTime(),
                DaotuRun.runId(player),
                DaotuOpening.hasOpenedQiao(player),
                faction,
                identity,
                contribution,
                reputation));
    }
}