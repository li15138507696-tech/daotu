package net.guzhenren.daotu;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * 事件注册（通过 {@code NeoForge.EVENT_BUS.register(DaotuEvents.class)}）。
 *
 * <p><b>v1.4.0</b>：觉醒系统删除后，原 {@code DaotuCombat} 的血战不退 / 杀神一击一并移除。
 *
 * <p><b>v1.8.0</b>：并入的 tianfu 词条整体移除，随之删掉
 * {@code DaotuCombatEffects}（暴击 / 闪避 / 减伤 / 吸血 / 增伤 / 每秒回复）——
 * 那些乘区的唯一来源就是词条，没有词条后它们永远读不到非零值。
 * 战斗侧现在只剩「受伤历练」，属性侧走 {@code DaotuRunAttributes} 的 AttributeModifier。
 */
public final class DaotuEvents {
    private DaotuEvents() {
    }

    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            DaotuRuntime.onTick(player);
        }
    }

    /**
     * 服务端就绪后打一行本体版本。
     *
     * <p>放在这里而不是构造器里：{@code EntityType} 注册表要等所有 mod 构造完才填好，
     * 构造期检测会误判成未知版本。只打一次，避免每个存档重复刷。
     */
    @SubscribeEvent
    public static void onServerStarted(net.neoforged.neoforge.event.server.ServerStartedEvent event) {
        DaotuCoreVersion version = DaotuCoreVersion.detect();
        DaotuMod.LOGGER.info("[道途] {}；本次会话按该版本的能力集运行", version.describe());
    }

    @SubscribeEvent
    public static void onLoggedIn(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            DaotuOpening.onLogin(player);
        }
    }

    @SubscribeEvent
    public static void onClone(PlayerEvent.Clone event) {
        if (event.getEntity() instanceof ServerPlayer player
                && event.getOriginal() instanceof ServerPlayer original) {
            DaotuOpening.onClone(player, original);
        }
    }

    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        // 受伤历练：被打也给一点，鼓励硬碰硬而非永远躲着
        if (event.getEntity() instanceof ServerPlayer sp && !sp.level().isClientSide()) {
            DaotuLiLian.onHurt(sp, event.getAmount());
        }
    }

    /** 击杀历练：生物死亡时，若最后一击来自玩家则结算。 */
    @SubscribeEvent
    public static void onLivingDeath(LivingDeathEvent event) {
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        if (event.getEntity() instanceof ServerPlayer) {
            return; // 玩家死亡不算「击杀历练」
        }
        LivingEntity victim = event.getEntity();
        if (event.getSource().getEntity() instanceof ServerPlayer killer) {
            DaotuLiLian.onKill(killer, victim);
        }
    }
}
