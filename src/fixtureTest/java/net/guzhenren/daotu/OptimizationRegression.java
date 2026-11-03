package net.guzhenren.daotu;

import java.util.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.ai.attributes.*;
import net.minecraft.nbt.CompoundTag;
import net.guzhenren.daotu.chronicle.*;
import net.guzhenren.daotu.chronicle.ChronicleModels.*;

/** Real production paths with explicit local fixtures; no Minecraft bootstrap or network. */
public final class OptimizationRegression {
    private static int checks;
    private static boolean candidate;
    private static final String ROOT=ChronicleModels.STORAGE_ROOT;
    public static void main(String[] args) {
        candidate=args[0].equals("candidate");attributes();draw();repository();
        System.out.println("PASS: "+checks+" local fixture checks ("+args[0]+"); no server started");
    }
    private static ServerPlayer player() {
        var p=new ServerPlayer();
        for(String key:DaotuRunAttributes.ALL_KEYS)p.attributes.put(key,new AttributeInstance());
        return p;
    }
    private static ResourceLocation id(String key){return ResourceLocation.fromNamespaceAndPath("daotu","run_"+key);}
    private static void attributes() {
        var p=player();
        for(String key:DaotuRunAttributes.ALL_KEYS)p.runAttrs.put(key,key.equals("fall_damage_multiplier")?-.2:.1);
        DaotuRunAttributes.apply(p);
        for(String key:DaotuRunAttributes.ALL_KEYS) {
            var m=p.attributes.get(key).getModifier(id(key));
            eq(p.runAttrs.get(key),m.amount(),"initial modifier "+key);
            check(m.operation()==(DaotuRunAttributes.isPercent(key)?AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL:AttributeModifier.Operation.ADD_VALUE),"operation "+key);
        }
        AttributeInstance.adds=0;AttributeInstance.removes=0;
        for(int i=0;i<10000;i++)DaotuRunAttributes.apply(p);
        System.out.println("BENCH attributePasses=10000 adds="+AttributeInstance.adds+" removes="+AttributeInstance.removes);
        if(candidate){eq(0,AttributeInstance.adds,"unchanged attributes not rewritten");eq(0,AttributeInstance.removes,"unchanged attributes not removed");}
        else {eq(140000,AttributeInstance.adds,"baseline repeated adds reproduced");eq(140000,AttributeInstance.removes,"baseline repeated removals reproduced");}
        p.runAttrs.put("max_health",.3);DaotuRunAttributes.apply(p);eq(.3,p.attributes.get("max_health").getModifier(id("max_health")).amount(),"changed value applied");
        var foreign=ResourceLocation.fromNamespaceAndPath("other","health");
        p.attributes.get("max_health").mods.put(foreign,new AttributeModifier(foreign,4,AttributeModifier.Operation.ADD_VALUE));
        p.runAttrs.remove("max_health");DaotuRunAttributes.apply(p);
        check(p.attributes.get("max_health").getModifier(id("max_health"))==null,"withdrawn modifier removed");
        check(p.attributes.get("max_health").getModifier(foreign)!=null,"other mod modifier retained");
        p.attributes.get("attack_damage").mods.remove(id("attack_damage"));DaotuRunAttributes.apply(p);
        eq(.1,p.attributes.get("attack_damage").getModifier(id("attack_damage")).amount(),"external removal repaired");
        p.attributes.get("attack_damage").mods.put(id("attack_damage"),new AttributeModifier(id("attack_damage"),.1,AttributeModifier.Operation.ADD_VALUE));
        DaotuRunAttributes.apply(p);check(p.attributes.get("attack_damage").getModifier(id("attack_damage")).operation()==AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL,"wrong operation repaired");
        p.runAttrs.put("c_legacy",5.0);p.runAttrs.put("unknown_saved_key",5.0);DaotuRunAttributes.apply(p);
        p.runAttrs.clear();DaotuRunAttributes.apply(p);
        for(String key:DaotuRunAttributes.ALL_KEYS)check(p.attributes.get(key).getModifier(id(key))==null,"reset clears "+key);
        p=player();p.level.client=true;p.runAttrs.put("max_health",.2);AttributeInstance.adds=0;DaotuRunAttributes.apply(p);
        eq(0,AttributeInstance.adds,"client apply is inert");
    }
    private static void draw() {
        var p=player();p.pool=1000;DaotuDraw.drawAll(p);
        eq(1,p.prompts,"one offer prompt");eq(candidate?1:2,p.packets,"no immediate duplicate packet");
        eq(1000,p.pool,"offer does not spend pool");eq(0,p.draws,"offer does not grant reward");
        check(!p.offer.isEmpty(),"pending offer saved");String offer=p.offer;
        DaotuDraw.drawAll(p);eqObj(offer,p.offer,"pending offer stable");eq(1,p.prompts,"pending offer not reopened");
        int packets=p.packets;check(!DaotuDraw.choose(p,99),"bad index rejected");eq(1000,p.pool,"bad index preserves pool");eq(packets,p.packets,"bad index sends no packet");
        check(DaotuDraw.choose(p,0),"valid choice accepted");eq(856,p.pool,"choice spends exactly once");eq(1,p.draws,"draw increments once");
        eq(1,p.history.size(),"one history entry");eq(.1,p.runAttrs.get("attack_damage"),"chosen reward applied");
        p=player();p.pool=1000;p.opened=false;DaotuDraw.drawAll(p);eq(0,p.packets,"closed aperture no packets");check(!DaotuDraw.choose(p,0),"closed aperture no choice");
        p=player();p.pool=1000;p.draws=100;DaotuDraw.drawAll(p);eq(0,p.packets,"rank cap sends no packets");
        p=player();p.pool=1000;p.draws=9;DaotuDraw.drawAll(p);check(p.offer.startsWith("special:"),"tenth draw keeps special reward");
    }
    private static ChronicleState state(UUID owner,long revision) {
        return new ChronicleState(owner,ChronicleModels.SCHEMA,revision,7,
            new FactionJournal(Set.of("a|b"),"a","b",100),
            new MeritArchive(20,30,Set.of("merit_a"),100),
            new ReputationJournal(-5,10,Set.of("rep_a"),100));
    }
    private static void repository() {
        var repo=new NbtChronicleRepository();var p=player();
        check(repo.load(p).isEmpty(),"missing journal empty");check(p.nbt.getAllKeys().isEmpty(),"read creates no storage");
        CompoundTag other=new CompoundTag();other.putString("sentinel","kept");p.nbt.put("tianfu",other);
        var first=state(p.getUUID(),0);check(repo.save(p,-1,first),"initial CAS save");eqObj(first,repo.load(p).orElseThrow(),"round trip preserves sets/negative reputation/run");
        var before=p.nbt.getCompound(ROOT);
        check(!repo.save(p,-1,first),"stale revision rejected");check(p.nbt.getCompound(ROOT)==before,"conflict does not replace root");
        expect(IllegalArgumentException.class,()->repo.save(p,0,state(UUID.randomUUID(),1)),"wrong owner rejected");
        CompoundTag.listReads=0;check(repo.save(p,0,state(p.getUUID(),1)),"existing CAS save");
        System.out.println("BENCH casJournalListDecodes="+CompoundTag.listReads);
        eq(candidate?0:3,CompoundTag.listReads,"CAS reads only necessary header");
        eqObj("kept",p.nbt.getCompound("tianfu").getString("sentinel"),"foreign root untouched");
        p.nbt.getCompound(ROOT).putInt("schema",ChronicleModels.SCHEMA+1);
        expect(IllegalStateException.class,()->repo.load(p),"future schema read rejected");
        expect(IllegalStateException.class,()->repo.save(p,1,state(p.getUUID(),2)),"future schema write rejected");
        p.nbt.getCompound(ROOT).putInt("schema",-1);expect(IllegalStateException.class,()->repo.save(p,1,state(p.getUUID(),2)),"negative schema rejected");
        p.nbt.getCompound(ROOT).putInt("schema",ChronicleModels.SCHEMA);
        var replacement=player();replacement.uuid=p.uuid;repo.copyForClone(p,replacement);
        replacement.nbt.getCompound(ROOT).getCompound("merit").putDouble("peak",999);
        eq(30,p.nbt.getCompound(ROOT).getCompound("merit").getDouble("peak"),"clone root deep copied");
        replacement.nbt.getCompound(ROOT).putLong("revision",9);repo.copyForClone(p,replacement);
        eq(9,replacement.nbt.getCompound(ROOT).getLong("revision"),"clone retains newer revision");
    }
    private static void eq(double expected,double actual,String m){check(Double.compare(expected,actual)==0,m+" actual="+actual+" expected="+expected);}
    private static void eqObj(Object expected,Object actual,String m){check(Objects.equals(expected,actual),m);}
    private static void check(boolean ok,String m){checks++;if(!ok)throw new AssertionError(m);}
    private static void expect(Class<? extends Throwable> type,Runnable call,String m){try{call.run();}catch(Throwable t){check(type.isInstance(t),m+" exception="+t);return;}check(false,m);}
}
