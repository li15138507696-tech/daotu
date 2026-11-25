"""Offline build for the core-linked 10.4 variant.

Compiles variants/core-10.4 against the exact nested guzhenren jar inside the
user-supplied 10.4 wrapper plus the local NeoForge 1.21.1 platform, then packages
build/libs/daotu-<version>.jar. Never starts Minecraft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / "variants" / "core-10.4"
PRODUCT_NAME = "道途"
DEFAULT_BASE = Path(r"D:\daima\mcmod\蛊真人本体\guzhenrn蛊真人模组本体10.4.jar")
DEFAULT_MC = Path(r"D:\game\mcmod\1\.minecraft")
DEFAULT_JDK = Path(r"C:\Users\ADMIN\.jdks\temurin-21")
INNER_ENTRY = "META-INF/jarjar/guzhenren-0.1-neoforge-1.21.1.jar"
EXPECTED_INNER_SHA256 = "B6D314D3810B8BC5FCFDBC4F588DB8721F0EFDFC14D27A0A06D88143A01FE2BC"
NEOFORGE = "21.1.249"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_version() -> str:
    props = VARIANT / "version.properties"
    text = props.read_text(encoding="utf-8-sig")
    m = re.search(r"(?m)^\s*version\s*=\s*(\S+)", text)
    if not m:
        raise SystemExit("variant version.properties has no version=")
    version = m.group(1)
    toml_path = VARIANT / "src/main/resources/META-INF/neoforge.mods.toml"
    raw = toml_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("variant mods.toml starts with a BOM (FML rejects it)")
    data = tomllib.loads(raw.decode("utf-8"))
    mod_version = data["mods"][0]["version"]
    if mod_version != version:
        raise SystemExit(f"version mismatch: version.properties={version} mods.toml={mod_version}")
    return version


def extract_core(base: Path) -> tuple[Path, str, str]:
    outer_sha = sha256(base)
    with zipfile.ZipFile(base) as z:
        if INNER_ENTRY not in z.namelist():
            raise SystemExit(f"{base} has no nested {INNER_ENTRY}")
        data = z.read(INNER_ENTRY)
    inner_sha = hashlib.sha256(data).hexdigest().upper()
    if inner_sha != EXPECTED_INNER_SHA256:
        raise SystemExit(f"nested guzhenren jar differs from the audited 10.4 build: {inner_sha}")
    out = ROOT / "build" / "core-10.4" / "guzhenren-core.jar"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.is_file() or sha256(out) != inner_sha:
        out.write_bytes(data)
    return out, outer_sha, inner_sha


def platform_classpath(mc_dir: Path) -> tuple[list[str], str]:
    libs = mc_dir / "libraries"
    best = None
    for f in (mc_dir / "versions").glob("*/*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            game_args = [x for x in data.get("arguments", {}).get("game", []) if isinstance(x, str)]
            if "--fml.neoForgeVersion" not in game_args or game_args[game_args.index("--fml.mcVersion") + 1] != "1.21.1":
                continue
            if best is None or len(data.get("libraries", [])) > len(best[0].get("libraries", [])):
                best = (data, game_args)
        except (ValueError, IndexError, OSError, AttributeError):
            continue
    if best is None:
        raise SystemExit("NeoForge 1.21.1 profile not found")
    data, game_args = best
    mc = game_args[game_args.index("--fml.mcVersion") + 1]
    form = game_args[game_args.index("--fml.neoFormVersion") + 1]
    neo = NEOFORGE
    cp = [
        libs / f"net/neoforged/neoforge/{neo}/neoforge-{neo}-client.jar",
        libs / f"net/minecraft/client/{mc}-{form}/client-{mc}-{form}-srg.jar",
        libs / f"net/neoforged/neoforge/{neo}/neoforge-{neo}-universal.jar",
    ]
    for jar in cp:
        if not jar.is_file():
            raise SystemExit(f"missing platform jar: {jar}")
    paths = [str(jar) for jar in cp]
    for lib in data.get("libraries", []):
        rel = lib.get("downloads", {}).get("artifact", {}).get("path", "")
        if rel and not rel.startswith("net/neoforged/neoforge/") and (libs / rel).is_file():
            paths.append(str(libs / rel))
    return paths, f"neoforge {neo} / minecraft {mc}-{form}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--minecraft-dir", type=Path, default=DEFAULT_MC)
    parser.add_argument("--jdk", type=Path, default=DEFAULT_JDK)
    args = parser.parse_args()

    if not args.base.is_file():
        raise SystemExit(f"missing 10.4 base jar: {args.base}")
    version = read_version()
    core, outer_sha, inner_sha = extract_core(args.base)
    cp, platform = platform_classpath(args.minecraft_dir)
    cp.append(str(core))

    sources = sorted((VARIANT / "src/main/java").rglob("*.java"))
    if not sources:
        raise SystemExit("no variant sources found")
    out = ROOT / "build" / "classes-core-10.4"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    q = lambda value: '"' + str(value).replace("\\", "/") + '"'
    argfile = ROOT / "build" / "core-104.args"
    argfile.write_text(
        "\n".join(
            ["-source", "21", "-target", "21", "-encoding", "UTF-8", "-proc:none", "-d", q(out), "-cp", q(";".join(cp))]
            + [q(p) for p in sources]
        ),
        encoding="utf-8",
    )
    javac = args.jdk / "bin/javac.exe"
    compiled = subprocess.run([str(javac), "@" + str(argfile)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    (ROOT / "build" / "javac-core-104.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
    if compiled.returncode:
        raise SystemExit(compiled.stdout + compiled.stderr[-8000:])

    mixin_cfg = json.loads((VARIANT / "src/main/resources/daotu.mixins.json").read_text(encoding="utf-8-sig"))
    mixin_dir = out / mixin_cfg["package"].replace(".", "/")
    missing_mixins = [n for n in mixin_cfg["mixins"] if not (mixin_dir / f"{n}.class").is_file()]
    if missing_mixins:
        raise SystemExit(f"mixin classes missing from javac output: {missing_mixins}")

    resources = VARIANT / "src/main/resources"
    jar = ROOT / "build/libs" / f"{PRODUCT_NAME}-{version}.jar"
    jar.parent.mkdir(parents=True, exist_ok=True)
    if jar.is_file():
        jar.unlink()
    # Fixed entry timestamps keep the artifact byte-reproducible across rebuilds.
    fixed_time = (2026, 11, 23, 0, 0, 0)
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        for tree in (out, resources):
            for path in sorted(tree.rglob("*")):
                if not path.is_file():
                    continue
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8-sig"))
                entry = zipfile.ZipInfo(path.relative_to(tree).as_posix(), date_time=fixed_time)
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o644 << 16
                z.writestr(entry, path.read_bytes())

    classes = sorted(out.rglob("*.class"))
    with zipfile.ZipFile(jar) as z:
        names = set(z.namelist())
        toml_bytes = z.read("META-INF/neoforge.mods.toml")
        jar_version = tomllib.loads(toml_bytes.decode("utf-8"))["mods"][0]["version"]
        probes = [
            "net/guzhenren/daotu/DaotuMod.class",
            "net/guzhenren/daotu/DaotuCoreVersion.class",
            "net/guzhenren/daotu/DaotuApply.class",
            "net/guzhenren/daotu/DaotuBuffs.class",
            "net/guzhenren/daotu/DaotuGrowthApply.class",
            "net/guzhenren/daotu/mixin/JingJieBaoCunProcedureMixin.class",
            "net/guzhenren/daotu/mixin/UikongqiaoquedingProcedureMixin.class",
            "META-INF/neoforge.mods.toml",
            "daotu.mixins.json",
            "assets/daotu/lang/zh_cn.json",
        ]
        missing = [p for p in probes if p not in names]
        if missing:
            raise SystemExit(f"jar probes missing: {missing}")
        if jar_version != version:
            raise SystemExit(f"jar version {jar_version} != {version}")
        if toml_bytes.startswith(b"\xef\xbb\xbf"):
            raise SystemExit("jar mods.toml has a BOM")
        if any(n.endswith(".java") or "Test" in n for n in names):
            raise SystemExit("jar contains sources or test classes")
        bad = [n for n in names if n.endswith(".class") and int.from_bytes(z.read(n)[6:8], "big") != 65]
        if bad:
            raise SystemExit(f"non-Java-21 class files: {bad[:5]}")

    report = {
        "product": PRODUCT_NAME,
        "version": version,
        "jar": str(jar),
        "sha256": sha256(jar),
        "sources": len(sources),
        "classes": len(classes),
        "mixins": mixin_cfg["mixins"],
        "baseJar": str(args.base),
        "baseSha256": outer_sha,
        "coreJarSha256": inner_sha,
        "platform": platform,
        "evidence": "Offline compilation/package checks; runtime verification recorded in build/runtime-core-104.json.",
    }
    (ROOT / "build" / "report-core-104.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS {len(sources)} sources, {len(classes)} classes, {len(mixin_cfg['mixins'])} mixins, {platform}")
    print(jar)
    print("SHA256 " + report["sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
