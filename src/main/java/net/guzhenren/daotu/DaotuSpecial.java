package net.guzhenren.daotu;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import java.util.List;
public final class DaotuSpecial {
 public static boolean isSpecial(String key) { return key != null && key.startsWith("special:"); }
 public static String labelOf(String key) { return "旧版本奖励（通用版不可用）"; }
 public static boolean grant(ServerPlayer player, String key, double amount) { return false; }
 public static List<DaotuDrawTable.Candidate> candidates(Player player,int draw,RandomSource rnd) { return DaotuDrawTable.candidates(player,draw,rnd); }
}
