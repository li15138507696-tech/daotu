package net.guzhenren.daotu;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.network.chat.Component;
import net.minecraft.nbt.Tag;
public final class DaotuOpening {
 public static void onLogin(ServerPlayer player) {
  boolean repaired = DaotuDraw.repairOffer(player);
  DaotuMigrate.migrateIfNeeded(player);
  if (repaired && DaotuRun.offer(player).isEmpty()) DaotuDraw.tryDraw(player);
  DaotuAttributes.sync(player);
  player.displayClientMessage(Component.literal("§6[道途] §e通用版已启用，输入 /daotu 打开道途。历练与属性成长独立于本体。"), false);
 }
 public static void onClone(ServerPlayer player,ServerPlayer original) {
  var data=original.getPersistentData();
  if(data.contains(DaotuData.ROOT,Tag.TAG_COMPOUND)) player.getPersistentData().put(DaotuData.ROOT,data.getCompound(DaotuData.ROOT).copy());
  DaotuAttributes.sync(player);
 }
}
