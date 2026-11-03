package net.guzhenren.daotu;

/** 道途试炼的稳定类型与网络快照。 */
public final class DaotuTrial {
    private DaotuTrial() {
    }

    public enum Type {
        COMBAT("combat", "百战试炼", "击杀敌对生物", 8),
        EXPLORATION("exploration", "行万里", "进入不同群系", 2),
        MEDITATION("meditation", "静坐修炼", "潜行静止修炼", 180);

        private final String id;
        private final String label;
        private final String description;
        private final int target;

        Type(String id, String label, String description, int target) {
            this.id = id;
            this.label = label;
            this.description = description;
            this.target = target;
        }

        public String id() { return id; }
        public String label() { return label; }
        public String description() { return description; }
        public int target() { return target; }

        public static Type byId(String id) {
            if (id == null) return null;
            for (Type type : values()) {
                if (type.id.equals(id)) return type;
            }
            return null;
        }
    }

    public record Snapshot(boolean ready, int milestone, int nextMilestone,
                           String type, int progress, int target, boolean completed) {
        public static Snapshot empty() {
            return new Snapshot(false, 0, 5, "", 0, 0, false);
        }
    }

    public record ProgressResult(boolean changed, boolean completed, double reward) {
        public static ProgressResult none() {
            return new ProgressResult(false, false, 0.0);
        }
    }
}