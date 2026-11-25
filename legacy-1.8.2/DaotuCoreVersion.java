package net.guzhenren.daotu;

/**
 * 本体版本识别。
 *
 * <p><b>为什么不能读 mod 版本号</b>：9.8 / 10.4 / 10.20 三个包的 {@code modId = guzhenren}、
 * {@code version = 0.1} 完全一样，FML 层面分不出来。
 *
 * <p>所以改用<b>内容指纹</b>（已实测核对）：
 *
 * <table border="1">
 *   <tr><th>版本</th><th>jiang_shi_gu_xiu</th><th>gu_xiu</th><th>FactionNpcManager</th></tr>
 *   <tr><td>9.8</td><td>有</td><td>无</td><td>无</td></tr>
 *   <tr><td>10.4</td><td>无</td><td>有</td><td>无</td></tr>
 *   <tr><td>10.20</td><td>无</td><td>有</td><td>有</td></tr>
 * </table>
 *
 * <p><b>为什么加这个</b>：{@code Core1020Adapter} 原来被无条件实例化，名字与文档却写着
 * 「仅适配 10.20 本体」。2026-11-01 对 9.8 做了逐层核对（类 / 411 个 PlayerVariables 字段 /
 * 两个 mixin 目标与签名 / markSyncDirty / 12 个流派 buff / XIUWEI 与 FUHUO），
 * 结果与 10.20 完全一致，所以 9.8 也安全；但这个边界以前只存在于文档里，
 * 代码里看不出来。现在把它显式化并打一条日志，避免以后有人按 10.20 的假设改坏 9.8。
 *
 * <p>检测结果缓存，但<b>只缓存确定的结论</b>：{@code EntityType} 注册表在类加载早期
 * 可能还没填完，那时两个 {@code hasEntity} 都会返回 false —— 如果连 {@link #UNKNOWN}
 * 一起缓存，就会把「暂时查不到」永久钉成「未知版本」。
 */
public enum DaotuCoreVersion {

    /** 9.8：独立扁平 jar，实体 699 个，含毛僵 / 跳僵，无 gu_xiu。 */
    V98("9.8", "独立扁平 jar；实体 699 个，含毛僵/跳僵，无 gu_xiu"),
    /** 10.4：jar-in-jar 包装，实体 656 个，含 gu_xiu。 */
    V104("10.4", "jar-in-jar 包装；实体 656 个，含 gu_xiu"),
    /** 10.20：本体与 10.4 同一个内嵌 jar，库层另加势力/任务/世界地图。 */
    V1020("10.20", "本体与 10.4 同一个内嵌 jar；库层含势力/任务/世界地图"),
    /** 认不出来。 */
    UNKNOWN("未知", "未匹配到已知指纹，按最保守方式跑");

    private final String label;
    private final String note;

    DaotuCoreVersion(String label, String note) {
        this.label = label;
        this.note = note;
    }

    public String label() {
        return label;
    }

    public String note() {
        return note;
    }

    private static DaotuCoreVersion cached;

    /** 检测本体版本；只缓存确定结论，{@link #UNKNOWN} 每次重算。 */
    public static DaotuCoreVersion detect() {
        if (cached != null) {
            return cached;
        }
        try {
            DaotuCoreVersion v;
            if (hasEntity("jiang_shi_gu_xiu")) {
                v = V98;
            } else if (hasClass("com.guzhenrenlibrary.faction.FactionNpcManager")) {
                v = V1020;
            } else if (hasEntity("gu_xiu")) {
                v = V104;
            } else {
                v = UNKNOWN;
            }
            if (v != UNKNOWN) {
                cached = v;
            }
            return v;
        } catch (Throwable t) {
            return UNKNOWN;
        }
    }

    private static boolean hasEntity(String id) {
        return net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.containsKey(
                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("guzhenren", id));
    }

    private static boolean hasClass(String name) {
        try {
            Class.forName(name, false, DaotuCoreVersion.class.getClassLoader());
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    /** 日志用的一行。 */
    public String describe() {
        return "本体版本 " + label + "（" + note + "）";
    }
}
