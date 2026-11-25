package net.guzhenren.daotu.client;
import net.guzhenren.daotu.net.DaotuStatePayload;
import net.minecraft.client.Minecraft;
/** Refresh the existing screen; open on an explicit request only when no screen is active. */
public final class DaotuClientHandler {
 private DaotuClientHandler() {}
 public static void receive(DaotuStatePayload payload) {
  Minecraft mc = Minecraft.getInstance();
  if (mc.screen instanceof DaotuViewScreen screen) { screen.applyState(payload); return; }
  if (payload.open() && mc.screen == null) mc.setScreen(new DaotuViewScreen(payload));
 }
}
