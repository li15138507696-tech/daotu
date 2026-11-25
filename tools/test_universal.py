"""Compile real production paths against local fixtures. Does not start Minecraft."""
from pathlib import Path
import argparse, json, subprocess

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--baseline',action='store_true')
p.add_argument('--baseline-source',type=Path,default=ROOT/'build/optimization-1.8.2/baseline/java')
args=p.parse_args()
variant='baseline' if args.baseline else 'candidate'
source=args.baseline_source if args.baseline else ROOT/'src/main/java'
out=ROOT/f'build/fixtures-{variant}'
out.mkdir(parents=True,exist_ok=True)
stubs={
'net/minecraft/core/Holder.java':'''package net.minecraft.core; public record Holder<T>(T value) {}''',
'net/minecraft/resources/ResourceLocation.java':'''package net.minecraft.resources; public record ResourceLocation(String namespace,String path) { public static ResourceLocation fromNamespaceAndPath(String n,String p){return new ResourceLocation(n,p);} }''',
'net/minecraft/world/entity/ai/attributes/Attribute.java':'''package net.minecraft.world.entity.ai.attributes; public record Attribute(String key) {}''',
'net/minecraft/world/entity/ai/attributes/AttributeModifier.java':'''package net.minecraft.world.entity.ai.attributes; import net.minecraft.resources.ResourceLocation; public record AttributeModifier(ResourceLocation id,double amount,Operation operation) { public enum Operation {ADD_VALUE,ADD_MULTIPLIED_TOTAL} }''',
'net/minecraft/world/entity/ai/attributes/AttributeInstance.java':'''package net.minecraft.world.entity.ai.attributes;
import java.util.*; import net.minecraft.resources.ResourceLocation;
public class AttributeInstance {
 public static int adds,removes; public final Map<ResourceLocation,AttributeModifier> mods=new HashMap<>();
 public AttributeModifier getModifier(ResourceLocation id){return mods.get(id);}
 public void removeModifier(ResourceLocation id){if(mods.remove(id)!=null)removes++;}
 public void addOrUpdateTransientModifier(AttributeModifier m){mods.put(m.id(),m);adds++;}
}''',
'net/minecraft/world/level/Level.java':'''package net.minecraft.world.level; public class Level { public boolean client; public boolean isClientSide(){return client;} }''',
'net/minecraft/world/entity/player/Player.java':'''package net.minecraft.world.entity.player;
import java.util.*; import net.minecraft.core.Holder; import net.minecraft.world.entity.ai.attributes.*;
import net.minecraft.world.level.Level; import net.minecraft.nbt.CompoundTag;
public class Player {
 public final Level level=new Level(); public final Map<String,AttributeInstance> attributes=new HashMap<>();
 public final Map<String,Double> runAttrs=new LinkedHashMap<>(); public final CompoundTag nbt=new CompoundTag();
 public UUID uuid=UUID.randomUUID(); public Level level(){return level;}
 public AttributeInstance getAttribute(Holder<Attribute> a){return attributes.get(a.value().key());}
 public CompoundTag getPersistentData(){return nbt;} public UUID getUUID(){return uuid;}
}''',
'net/minecraft/server/level/ServerPlayer.java':'''package net.minecraft.server.level;
import net.minecraft.world.entity.player.Player; import net.minecraft.util.RandomSource; import net.minecraft.network.chat.Component;
public class ServerPlayer extends Player {
 public boolean opened=true;public double pool,zhuan=1;public int draws,offerDraw,prompts,packets,lastSentDraws;
 public String offer="";public final java.util.List<String> history=new java.util.ArrayList<>();
 public RandomSource getRandom(){return new RandomSource();} public void displayClientMessage(Component c,boolean actionbar){}
}''',
'net/minecraft/util/RandomSource.java':'''package net.minecraft.util; public class RandomSource {public int nextInt(int bound){return 0;} }''',
'net/minecraft/network/chat/Component.java':'''package net.minecraft.network.chat; public record Component(String text){public static Component literal(String t){return new Component(t);} }''',
'net/guzhenren/daotu/DaotuMod.java':'''package net.guzhenren.daotu; public class DaotuMod {public static final String MODID="daotu";public static final Log LOGGER=new Log();public static class Log {public void warn(String m,Object...args){} } }''',
'net/guzhenren/daotu/DaotuRun.java':'''package net.guzhenren.daotu;
import java.util.*;import net.minecraft.world.entity.player.Player;import net.minecraft.server.level.ServerPlayer;
public class DaotuRun {
 public static double attr(Player p,String k){return p.runAttrs.getOrDefault(k,0.0);}public static void setAttr(Player p,String k,double v){p.runAttrs.put(k,v);}
 public static Map<String,Double> attrs(Player p){return new LinkedHashMap<>(p.runAttrs);}
 public static double zhuanshu(ServerPlayer p){return p.zhuan;}public static int draws(ServerPlayer p){return p.draws;}
 public static String offer(ServerPlayer p){return p.offer;}public static int offerDraw(ServerPlayer p){return p.offerDraw;}
 public static double pool(ServerPlayer p){return p.pool;}public static double thresholdOf(ServerPlayer p){return 144;}
 public static void setPool(ServerPlayer p,double v){p.pool=v;}public static void setDraws(ServerPlayer p,int v){p.draws=v;}
 public static void setOffer(ServerPlayer p,int d,String s){p.offerDraw=d;p.offer=s;}public static void clearOffer(ServerPlayer p){p.offer="";p.offerDraw=0;}
 public static void addHistory(ServerPlayer p,String s){p.history.add(s);}
}''',
'net/guzhenren/daotu/DaotuOpening.java':'''package net.guzhenren.daotu;import net.minecraft.server.level.ServerPlayer;public class DaotuOpening {public static boolean hasOpenedQiao(ServerPlayer p){return p.opened;} }''',
'net/guzhenren/daotu/DaotuNet.java':'''package net.guzhenren.daotu;import net.minecraft.server.level.ServerPlayer;public class DaotuNet {public static void promptChoice(ServerPlayer p){p.prompts++;p.packets++;}public static void sendState(ServerPlayer p){p.packets++;p.lastSentDraws=p.draws;} }''',
'net/guzhenren/daotu/DaotuAttributes.java':'''package net.guzhenren.daotu;import net.minecraft.world.entity.player.Player;public class DaotuAttributes {public static void sync(Player p){DaotuRunAttributes.apply(p);} }''',
'net/guzhenren/daotu/DaotuDrawTable.java':'''package net.guzhenren.daotu;import java.util.*;import net.minecraft.server.level.ServerPlayer;import net.minecraft.util.RandomSource;
public class DaotuDrawTable {public static final double KNOCKBACK_CAP=1,SPEED_CAP=1,ATTACK_SPEED_CAP=2,HEALTH_CAP=10,SCALE_CAP=3,STEP_CAP=3;
public record Candidate(String key,String label,double amount,boolean percent){}
public static List<Candidate> candidates(ServerPlayer p,int n,RandomSource r){return List.of(new Candidate("attack_damage","力量",.1,true));}}
''',
'net/guzhenren/daotu/DaotuSpecial.java':'''package net.guzhenren.daotu;import java.util.*;import net.minecraft.server.level.ServerPlayer;import net.minecraft.util.RandomSource;
public class DaotuSpecial {public static boolean isSpecial(String k){return k.startsWith("special:");}public static String labelOf(String k){return k;}public static void grant(ServerPlayer p,String k,double a){p.runAttrs.put(k,a);} public static List<DaotuDrawTable.Candidate> candidates(ServerPlayer p,int n,RandomSource r){return DaotuDrawTable.candidates(p,n,r);}}
''',
'net/minecraft/nbt/Tag.java':'''package net.minecraft.nbt;public interface Tag {int TAG_COMPOUND=10,TAG_LIST=9,TAG_STRING=8,TAG_INT=3,TAG_LONG=4,TAG_DOUBLE=6;}''',
'net/minecraft/nbt/StringTag.java':'''package net.minecraft.nbt;public record StringTag(String value) implements Tag {public static StringTag valueOf(String s){return new StringTag(s);}}''',
'net/minecraft/nbt/ListTag.java':'''package net.minecraft.nbt;public class ListTag extends java.util.ArrayList<StringTag> implements Tag {public String getString(int i){return get(i).value();}}''',
'net/minecraft/nbt/CompoundTag.java':'''package net.minecraft.nbt;import java.util.*;
public class CompoundTag implements Tag {
 public static int listReads;private final Map<String,Object> values=new HashMap<>();
 public boolean contains(String k,int t){Object v=values.get(k);return switch(t){case 10->v instanceof CompoundTag;case 9->v instanceof ListTag;case 8->v instanceof String;case 3->v instanceof Integer;case 4->v instanceof Long;case 6->v instanceof Double;default->false;};}
 public CompoundTag getCompound(String k){return values.get(k) instanceof CompoundTag t?t:new CompoundTag();}
 public ListTag getList(String k,int type){listReads++;return values.get(k) instanceof ListTag t?t:new ListTag();}
 public int getInt(String k){return values.get(k) instanceof Number n?n.intValue():0;}
 public long getLong(String k){return values.get(k) instanceof Number n?n.longValue():0;}
 public double getDouble(String k){return values.get(k) instanceof Number n?n.doubleValue():0;}
 public String getString(String k){return values.get(k) instanceof String s?s:"";}
 public void put(String k,Tag t){values.put(k,t);}public void putString(String k,String v){values.put(k,v);}
 public void putInt(String k,int v){values.put(k,v);}public void putLong(String k,long v){values.put(k,v);}public void putDouble(String k,double v){values.put(k,v);}
 public Set<String> getAllKeys(){return values.keySet();}
 public CompoundTag copy(){CompoundTag c=new CompoundTag();values.forEach((k,v)->{if(v instanceof CompoundTag t)c.values.put(k,t.copy());else if(v instanceof ListTag l){ListTag n=new ListTag();n.addAll(l);c.values.put(k,n);}else c.values.put(k,v);});return c;}
 @Override public boolean equals(Object v){return v instanceof CompoundTag t&&values.equals(t.values);}@Override public int hashCode(){return values.hashCode();}
}'''
}
stubs['net/guzhenren/daotu/DaotuData.java'] = """package net.guzhenren.daotu;
import net.minecraft.nbt.CompoundTag;import net.minecraft.server.level.ServerPlayer;import java.util.function.Consumer;
public class DaotuData {public static final String ROOT="daotu"; static CompoundTag root(ServerPlayer p,boolean create){if(!p.nbt.contains(ROOT,10)&&create)p.nbt.put(ROOT,new CompoundTag());return p.nbt.contains(ROOT,10)?p.nbt.getCompound(ROOT):null;}
static void update(ServerPlayer p,Consumer<CompoundTag> c){c.accept(root(p,true));}public static boolean migrated(ServerPlayer p){var t=root(p,false);return t!=null&&t.getInt("migrated")==1;}public static void markMigrated(ServerPlayer p){root(p,true).putInt("migrated",1);}public static String origin(ServerPlayer p){var t=root(p,false);return t==null?"":t.getString("origin");}}
"""
stubs['net/minecraft/nbt/CompoundTag.java']=stubs['net/minecraft/nbt/CompoundTag.java'].replace('public boolean contains(String k,int t)', 'public boolean contains(String k){return values.containsKey(k);} public boolean contains(String k,int t)')
stubs['net/guzhenren/daotu/DaotuRun.java']=stubs['net/guzhenren/daotu/DaotuRun.java'].replace('public static void addHistory(ServerPlayer p,String s)', 'public static java.util.Map<String,Double> attrs(ServerPlayer p){return p.runAttrs;} public static java.util.List<String> history(ServerPlayer p){return p.history;} public static void addHistory(ServerPlayer p,String s)')
keys=['attack_damage' ,'max_health','movement_speed','attack_speed','armor_toughness','max_absorption','knockback_resistance','fall_damage_multiplier','luck','safe_fall_distance','attack_knockback','oxygen_bonus','step_height','scale']
stubs['net/minecraft/world/entity/ai/attributes/Attributes.java']='package net.minecraft.world.entity.ai.attributes;import net.minecraft.core.Holder;public class Attributes {'+''.join(f'public static final Holder<Attribute> {k.upper()}=new Holder<>(new Attribute("{k}"));' for k in keys)+'}'
paths=[]
for name,text in stubs.items():
    path=out/'stubs'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8');paths.append(path)
real=['DaotuRunAttributes.java','DaotuDraw.java','DaotuMigrate.java','chronicle/NbtChronicleRepository.java','chronicle/ChronicleModels.java','chronicle/ChronicleTables.java','chronicle/ChronicleRepository.java']
paths += [source/'net/guzhenren/daotu'/name for name in real]
test=(ROOT/'src/fixtureTest/java/net/guzhenren/daotu/OptimizationRegression.java').read_text(encoding='utf-8')
test=test.replace('p=player();p.pool=1000;p.opened=false;DaotuDraw.drawAll(p);eq(0,p.packets,"closed aperture no packets");check(!DaotuDraw.choose(p,0),"closed aperture no choice");','').replace('eq(0,p.packets,"rank cap sends no packets")','check(p.packets > 0,"universal has no rank cap")').replace('check(p.offer.startsWith("special:"),"tenth draw keeps special reward")','check(!p.offer.startsWith("special:"),"tenth draw uses independent attributes")')
test=test.replace('candidate=args[0].equals("candidate");attributes();draw();repository();','candidate=args[0].equals("candidate");attributes();draw();repository();universal184();')
test=test.replace('    private static ChronicleState state(', r'''    private static void universal184() {
        var p=player(); p.pool=144; p.offerDraw=1;
        p.offer="talent:old=1=0,attack_damage=0.1=1,special:qiyun=2=0,luck=2=0";
        check(DaotuDraw.repairOffer(p),"mixed offer repaired");
        eqObj("attack_damage=0.1=1,luck=2=0",p.offer,"valid rows kept in order");
        check(p.nbt.getCompound("daotu").getString("universal184LegacyOffer").startsWith("talent:"),"original backed up");
        check(!DaotuDraw.repairOffer(p),"repair idempotent");
        p=player();p.pool=144;p.offerDraw=1;p.offer="talent:old=1=0,attack_damage=NaN=1,luck=-1=0";
        check(!DaotuDraw.choose(p,0),"invalid offer refuses old index");
        eq(144,p.pool,"repair spends no pool");check(!p.offer.contains("talent:"),"all invalid regenerated");
        p=player();p.pool=144;p.offerDraw=1;p.offer="max_health=0.1=1";p.runAttrs.put("max_health",10.0);
        check(!DaotuDraw.choose(p,0),"cap repairs no-op reward");eq(144,p.pool,"capped reward preserves pool");
        p=player();var root=new CompoundTag();root.putString("origin","sanxiu");p.nbt.put("daotu",root);
        p.pool=144;p.offerDraw=1;p.offer="attack_damage=0.1=1";
        check(!DaotuMigrate.migrateIfNeeded(p),"pending offer defers migration");eq(0,p.draws,"defer preserves draw index");
        check(DaotuDraw.choose(p,0),"pending offer can be claimed");eq(8,p.draws,"deferred migration fills legacy entitlement");eq(8,p.history.size(),"migration history and claim recorded");eq(8,p.lastSentDraws,"published state includes deferred conversion");
        eq(0,p.pool,"only chosen offer spends pool");eqObj("sanxiu",p.nbt.getCompound("daotu").getString("origin"),"legacy origin preserved");
        check(!DaotuMigrate.migrateIfNeeded(p),"migration idempotent");eq(8,p.draws,"repeat migration does not duplicate");
        p=player();root=new CompoundTag();var rank=new CompoundTag();rank.putInt("blade",3);root.put("rank",rank);p.nbt.put("daotu",root);p.draws=5;
        check(DaotuMigrate.migrateIfNeeded(p),"legacy rank migrates");eq(12,p.draws,"existing draws count toward rank entitlement");
    }
    private static ChronicleState state(''')
testpath=out/'OptimizationRegression.java';testpath.write_text(test,encoding='utf-8');paths.append(testpath)
classes=out/'classes';classes.mkdir(exist_ok=True)
jdk=Path(r'C:\Users\ADMIN\.jdks\temurin-21\bin')
compile=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-proc:none','-d',str(classes),*map(str,paths)],capture_output=True,text=True,encoding='utf-8',errors='replace')
if compile.returncode: raise SystemExit(compile.stdout+compile.stderr)
run=subprocess.run([str(jdk/'java.exe'),'-Dfile.encoding=UTF-8','-cp',str(classes),'net.guzhenren.daotu.OptimizationRegression',variant],capture_output=True,text=True,encoding='utf-8',errors='replace')
(out/'result.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
print(run.stdout+run.stderr,end='')
if run.returncode: raise SystemExit(run.returncode)
