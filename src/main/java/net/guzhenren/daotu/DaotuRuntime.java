package net.guzhenren.daotu;

import net.minecraft.server.level.ServerPlayer;

/** Once-per-second experience/buff maintenance, with live attribute reconciliation every five seconds. */
public final class DaotuRuntime {
    private static final int PERIOD = 20;

    private DaotuRuntime() { }

    public static void onTick(ServerPlayer player) {
        if (player.tickCount % PERIOD != 0) return;
        try {
            boolean opened = DaotuOpening.hasOpenedQiao(player);
            if (opened) {
                DaotuLiLian.onSecond(player);
                // Native procedures can clear all effects: missing reward buffs still recover each second.
                DaotuBuffs.maintain(player);
            }
            // No luck-cap source has existed since 1.4.0. Do not fetch native data for that dead path.
            if (player.tickCount % (PERIOD * 5) == 0) {
                DaotuAttributes.sync(player);
            }
        } catch (Throwable t) {
            DaotuMod.LOGGER.warn("daotu onTick 失败（已忽略）", t);
        }
    }
}
