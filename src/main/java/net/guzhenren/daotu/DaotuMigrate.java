package net.guzhenren.daotu;

import java.util.Map;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/**
 * 旧存档迁移：1.0.0「出身」/ 1.1.0「十六路阶位」→ 1.3.0「肉鸽抽选」。
 *
 * <p>v2 取消了 16 路阶位，但老玩家不该白玩。折算口径：
 * <ul>
 *   <li>读过「出身」的（1.0.0 存档）：按出身强弱给若干<b>起始抽选次数</b>；</li>
 *   <li>有 16 路阶位的（1.1.0 / 1.2.x 存档）：取<b>最高阶</b>折算成抽选次数；</li>
 *   <li>两者都没有：新号，从 0 抽开始。</li>
 * </ul>
 *
 * <p><b>为什么折算成抽选次数而不是直接给属性</b>：抽选次数是本局唯一的成长刻度，
 * 折算成次数后玩家可以自己抽、自己选，行为与正常游玩完全一致，
 * 不会出现「老存档一登录就带着一堆看不懂的属性」。
 *
 * <p><b>幂等</b>：靠 {@code migrated} 标记，重复登录不会二次折算。
 *
 * <p><b>不追溯扣道痕</b>：v1 的阶位奖励发过的道痕就留在玩家身上，
 * 只有 v2 之后抽出来的道痕才记进 {@code run/ledger} 并在转世时扣回。
 */
public final class DaotuMigrate {

    /** 旧出身 id → 折算的起始抽选次数。 */
    private static final Map<String, Integer> ORIGIN_TO_DRAWS = Map.ofEntries(
            Map.entry("xiongjia_kuangtu", 4),
            Map.entry("zuitu", 4),
            Map.entry("tianwai_yigu", 4),
            Map.entry("baijia_liehu", 8),
            Map.entry("shangdui_yigu", 8),
            Map.entry("guyue_pangzhi", 8),
            Map.entry("dushi_fang", 8),
            Map.entry("guyue_dixi", 8),
            Map.entry("baijia_shaozhu", 8),
            Map.entry("lianxuan_xuetu", 8),
            Map.entry("jianmen_zhujian", 8),
            Map.entry("bingxue_waimen", 8),
            Map.entry("sanxiu", 8),
            Map.entry("hundao_yishi", 12),
            Map.entry("daoyou", 12),
            Map.entry("qiankun_sanyi", 12));

    /** v1 阶位 → 折算抽选次数（最高阶是 5）。 */
    private static final int[] RANK_TO_DRAWS = {0, 4, 8, 12, 16, 20};

    private DaotuMigrate() {
    }

    /**
     * 若检测到旧存档，折算成起始抽选次数。
     *
     * @return true 表示本次做了迁移
     */
    public static boolean migrateIfNeeded(ServerPlayer player) {
        if (DaotuData.migrated(player) || !DaotuRun.offer(player).isEmpty()) return false;
        String origin = DaotuData.origin(player);
        int rank = highestLegacyRank(player);
        if (rank <= 0 && origin.isEmpty()) return false;
        int target = rank > 0 ? RANK_TO_DRAWS[Math.min(rank, 5)] : ORIGIN_TO_DRAWS.getOrDefault(origin, 4);
        // Existing draws count toward the legacy entitlement, preventing duplicate conversion.
        int existing = DaotuRun.draws(player);
        int count = Math.max(0, target - existing);
        // Unnumbered pre-existing growth cannot be distinguished safely from old conversion.
        if (existing == 0 && (!DaotuRun.attrs(player).isEmpty() || !DaotuRun.history(player).isEmpty())) count = 0;
        var original = DaotuData.root(player, false).copy();
        try {
            DaotuDraw.replayForMigration(player, count);
            DaotuData.markMigrated(player);
        } catch (RuntimeException ex) {
            player.getPersistentData().put(DaotuData.ROOT, original);
            DaotuMod.LOGGER.warn("旧成长折算失败，原数据已恢复，下次重试", ex);
            return false;
        }
        DaotuAttributes.sync(player);
        if (count > 0) player.displayClientMessage(Component.literal(
                "§6[道途] 旧成长已折算为 " + count + " 次独立属性成长。"), false);
        return count > 0;
    }

    /** 读旧存档里 16 路的最大阶位（v2 起不再写入，只用于迁移）。 */
    private static int highestLegacyRank(ServerPlayer player) {
        var tag = DaotuData.root(player, false);
        if (tag == null || !tag.contains("rank", net.minecraft.nbt.Tag.TAG_COMPOUND)) {
            return 0;
        }
        var rankTag = tag.getCompound("rank");
        int max = 0;
        for (String key : rankTag.getAllKeys()) {
            max = Math.max(max, rankTag.getInt(key));
        }
        return Math.min(max, 5);
    }
}
