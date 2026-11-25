"""Static compatibility audit: core-linked daotu 1.8.5-10.4 against the base mod 10.4.

Reads the exact 10.4 wrapper jar supplied by the user, extracts its nested
guzhenren jar, and checks every base-mod symbol the variant source references.
Never starts Minecraft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / "variants" / "core-10.4"
DEFAULT_BASE = Path(r"D:\daima\mcmod\蛊真人本体\guzhenrn蛊真人模组本体10.4.jar")
DEFAULT_JDK = Path(r"C:\Users\ADMIN\.jdks\temurin-21")
INNER_ENTRY = "META-INF/jarjar/guzhenren-0.1-neoforge-1.21.1.jar"

# Pinned fingerprints of the audited 10.4 package.
EXPECTED_OUTER_SHA256 = "2C6A1481BB1116AD85BB62DF56298FDADE3E2987AD7BD44604079439DAEBE9D2"
EXPECTED_INNER_SHA256 = "B6D314D3810B8BC5FCFDBC4F588DB8721F0EFDFC14D27A0A06D88143A01FE2BC"

EFFECT_IDS = [
    "shuidaozengfu",
    "yudaoguchongweilizengfu",
    "qidaoguchongweilizengfu",
    "jiandaoshanghaizengfu",
    "lvdaozengfu",
    "jindaozengfu",
    "yandaozengfu",
    "leidaozengshang",
    "weilizengjia",
    "daligubuff",
    "tiexue",
    "leishen",
]

# Direct field reads/writes in the variant source (dynamic table fields are
# discovered from string literals below).
DIRECT_FIELDS = [
    "shouyuan",
    "zhuanshu",
    "shenfen",
    "shili",
    "GongXianZhi",
    "mingsheng",
    "qiyun_shangxian",
]

FIELD_LITERAL = re.compile(r'"(daohen|dahen|liupai)_[a-z0-9_]+"')
DIRECT_ACCESS = re.compile(r"\bv\.([A-Za-z_][A-Za-z0-9_]*)")
JAVAP_FIELD = re.compile(r"^\s+(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?([\w.$]+)\s+([A-Za-z_$][\w$]*);$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(cmd)}\n{result.stdout}{result.stderr}")
    return result.stdout + result.stderr


def javap(javap_exe: Path, jar: Path, class_name: str) -> str:
    return run([str(javap_exe), "-p", "-classpath", str(jar), class_name])


def class_entries(name: str):
    """Yield jar entry candidates, covering nested classes written with '.' in imports."""
    yield name.replace(".", "/") + ".class"
    segments = name.split(".")
    for i in range(1, len(segments)):
        yield "/".join(segments[:i]) + "$" + "$".join(segments[i:]) + ".class"


class Audit:
    def __init__(self) -> None:
        self.checks: list[dict[str, object]] = []

    def check(self, name: str, ok: bool, detail: object = "") -> bool:
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}" if detail else ""))
        return ok

    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c["ok"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--jdk", type=Path, default=DEFAULT_JDK)
    args = parser.parse_args()

    base: Path = args.base
    javap_exe = args.jdk / "bin" / "javap.exe"
    if not base.is_file():
        raise SystemExit(f"missing base jar: {base}")
    if not javap_exe.is_file():
        raise SystemExit(f"missing javap: {javap_exe}")

    audit = Audit()
    outer_sha = sha256(base)
    audit.check("base 10.4 outer sha256 pinned", outer_sha == EXPECTED_OUTER_SHA256, outer_sha)

    work = ROOT / "build" / "core-10.4"
    work.mkdir(parents=True, exist_ok=True)
    core = work / "guzhenren-core.jar"
    with zipfile.ZipFile(base) as z:
        names = set(z.namelist())
        audit.check("base contains nested guzhenren jar", INNER_ENTRY in names)
        data = z.read(INNER_ENTRY)
    inner_sha = hashlib.sha256(data).hexdigest().upper()
    audit.check("nested guzhenren sha256 pinned", inner_sha == EXPECTED_INNER_SHA256, inner_sha)
    if not core.is_file() or sha256(core) != inner_sha:
        core.write_bytes(data)

    with zipfile.ZipFile(core) as z:
        core_names = set(z.namelist())
        inner_lang = json.loads(z.read("assets/guzhenren/lang/en_us.json").decode("utf-8-sig"))

    # ---- 1. Classes referenced from source ----
    core_classes: set[str] = set()
    for path in (VARIANT / "src/main/java").rglob("*.java"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for imp in re.findall(r"^import\s+(?:static\s+)?(net\.guzhenren\.[\w.]+);", text, re.M):
            if imp.startswith("net.guzhenren.daotu."):
                continue
            core_classes.add(imp)
    missing_classes = []
    for name in sorted(core_classes):
        if not any(entry in core_names for entry in class_entries(name)):
            missing_classes.append(name)
    audit.check("source-referenced core classes exist", not missing_classes, sorted(core_classes) if not missing_classes else missing_classes)

    # ---- 2. PlayerVariables fields / methods ----
    pv = javap(javap_exe, core, "net.guzhenren.network.GuzhenrenModVariables$PlayerVariables")
    fields: dict[str, str] = {}
    for line in pv.splitlines():
        m = JAVAP_FIELD.match(line)
        if m and not m.group(2).startswith("_"):
            fields[m.group(2)] = m.group(1)
    audit.check("PlayerVariables field count == 411", len(fields) == 411, len(fields))
    audit.check("PlayerVariables.markSyncDirty() present", "public void markSyncDirty();" in pv)

    holder = javap(javap_exe, core, "net.guzhenren.network.GuzhenrenModVariables")
    audit.check(
        "GuzhenrenModVariables.PLAYER_VARIABLES present",
        "public static final java.util.function.Supplier<net.neoforged.neoforge.attachment.AttachmentType<net.guzhenren.network.GuzhenrenModVariables$PlayerVariables>> PLAYER_VARIABLES;" in holder,
    )

    dynamic: set[str] = set()
    for path in (VARIANT / "src/main/java").rglob("*.java"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        dynamic.update(m.group(0).strip('"') for m in FIELD_LITERAL.finditer(text))
        dynamic.update(m.group(1) for m in DIRECT_ACCESS.finditer(text))
    dynamic.discard("markSyncDirty")
    audit.check("dynamic core field names discovered", len(dynamic) >= 60, len(dynamic))
    missing_fields = sorted(n for n in dynamic if n not in fields)
    audit.check("all referenced PlayerVariables fields exist", not missing_fields, missing_fields or len(dynamic))
    wrong_type = sorted(f"{n}:{fields[n]}" for n in dynamic if n in fields and fields[n] != "double" and n not in ("shenfen", "shili"))
    audit.check("numeric fields are double", not wrong_type, wrong_type)
    string_fields = sorted(f"{n}:{fields.get(n)}" for n in ("shenfen", "shili") if fields.get(n) != "java.lang.String")
    audit.check("shenfen/shili are String", not string_fields, string_fields)

    # ---- 3. Mixin targets and static members ----
    jj = javap(javap_exe, core, "net.guzhenren.procedures.JingJieBaoCunProcedure")
    audit.check(
        "JingJieBaoCunProcedure.execute(Event, LevelAccessor, Entity) private static",
        "private static void execute(net.neoforged.bus.api.Event, net.minecraft.world.level.LevelAccessor, net.minecraft.world.entity.Entity);" in jj,
    )
    uq = javap(javap_exe, core, "net.guzhenren.procedures.UikongqiaoquedingProcedure")
    audit.check(
        "UikongqiaoquedingProcedure.execute(LevelAccessor, Entity) public static",
        "public static void execute(net.minecraft.world.level.LevelAccessor, net.minecraft.world.entity.Entity);" in uq,
    )
    rules = javap(javap_exe, core, "net.guzhenren.init.GuzhenrenModGameRules")
    audit.check(
        "GuzhenrenModGameRules.XIUWEI is Key<BooleanValue>",
        "public static net.minecraft.world.level.GameRules$Key<net.minecraft.world.level.GameRules$BooleanValue> XIUWEI;" in rules,
    )
    effects = javap(javap_exe, core, "net.guzhenren.init.GuzhenrenModMobEffects")
    audit.check(
        "GuzhenrenModMobEffects.FUHUO is MobEffect holder",
        "public static final net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.effect.MobEffect, net.minecraft.world.effect.MobEffect> FUHUO;" in effects,
    )

    # ---- 4. Registry ids / version fingerprint ----
    missing_effects = [e for e in EFFECT_IDS if f"effect.guzhenren.{e}" not in inner_lang]
    audit.check("12 whitelist effects registered", not missing_effects, missing_effects or 12)
    audit.check("entity guzhenren:gu_xiu registered", "entity.guzhenren.gu_xiu" in inner_lang)
    audit.check(
        "entity guzhenren:jiang_shi_gu_xiu absent (not 9.8)",
        "entity.guzhenren.jiang_shi_gu_xiu" not in inner_lang,
    )
    with zipfile.ZipFile(base) as z:
        outer_names = set(z.namelist())
    faction_present = any(n.startswith("com/guzhenrenlibrary/faction/FactionNpcManager") for n in outer_names)
    audit.check("FactionNpcManager absent (not 10.20)", not faction_present)
    audit.check("library layer present", "com/guzhenrenlibrary/GuzhenrenLibrary.class" in outer_names)
    detected = "V98" if "entity.guzhenren.jiang_shi_gu_xiu" in inner_lang else (
        "V1020" if faction_present else ("V104" if "entity.guzhenren.gu_xiu" in inner_lang else "UNKNOWN")
    )
    audit.check("DaotuCoreVersion.detect() would report 10.4", detected == "V104", detected)

    report = {
        "base": str(base),
        "outerSha256": outer_sha,
        "innerJar": INNER_ENTRY,
        "innerSha256": inner_sha,
        "playerVariablesFields": len(fields),
        "referencedFields": len(dynamic),
        "coreClasses": sorted(core_classes),
        "detected": detected,
        "checks": audit.checks,
        "pass": audit.fail_count() == 0,
    }
    (ROOT / "build" / "audit-core-104.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'PASS' if report['pass'] else 'FAIL'}: {len(audit.checks) - audit.fail_count()}/{len(audit.checks)} checks; detected={detected}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
