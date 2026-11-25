package net.guzhenren.daotu;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Monster;

/** 服务端试炼接取、进度与完成流程。 */
public final class DaotuTrialService {
    private DaotuTrialService() {
    }

    public static DaotuTrial.Snapshot snapshot(ServerPlayer player) {
        return DaotuRun.trialSnapshot(player);
    }

    public static void accept(ServerPlayer player, int runId, int milestone, String typeId) {
        if (!DaotuOpening.hasOpenedQiao(player) || runId != DaotuRun.runId(player)) return;
        DaotuTrial.Type type = DaotuTrial.Type.byId(typeId);
        DaotuTrial.Snapshot state = DaotuRun.trialSnapshot(player);
        if (type == null || !state.ready() || state.nextMilestone() != milestone) return;
        if (!DaotuRun.acceptTrial(player, milestone, type.id())) return;
        player.displayClientMessage(net.minecraft.network.chat.Component.literal(
                "§6[道途] §e已接取 " + type.label() + "（第 " + milestone + " 抽节点）"), false);
        DaotuNet.sendState(player);
    }

    /** 仅玩家最后一击击杀敌对 Monster 才计入战斗试炼。 */
    public static void onKill(ServerPlayer player, LivingEntity victim) {
        if (victim instanceof Monster) record(player, 1, null, false);
    }

    /** 仅接取后首次到访的本世新群系计入探索试炼。 */
    public static void onBiome(ServerPlayer player, String biome) {
        if (biome == null || biome.isEmpty()) return;
        String visited = DaotuData.getString(player, "biomes", "");
        if (visited.contains("|" + biome + "|")) return;
        record(player, 0, biome, false);
    }

    /** 合格的静止潜行秒数；进度每五秒同步一次。 */
    public static void onMeditationSecond(ServerPlayer player, boolean meditating) {
        if (meditating) record(player, 1, null, true);
    }

    private static void record(ServerPlayer player, int delta, String biome, boolean meditation) {
        if (!DaotuOpening.hasOpenedQiao(player)) return;
        int milestone = DaotuRun.trialMilestone(player);
        if (milestone <= 0 || DaotuRun.trialType(player).isEmpty()
                || DaotuRun.trialCompleted(player)) return;
        DaotuTrial.ProgressResult result =
                DaotuRun.advanceTrial(player, milestone, delta, biome);
        if (!result.changed()) return;
        if (result.completed()) {
            player.displayClientMessage(net.minecraft.network.chat.Component.literal(
                    "§6[道途] §a试炼完成 · 历练 +" + Math.round(result.reward())), false);
            DaotuDraw.drawAll(player);
            DaotuNet.sendState(player);
        } else if (!meditation || DaotuRun.trialProgress(player) % 5 == 0) {
            DaotuNet.sendState(player);
        }
    }
}