from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, tomllib, zipfile
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description='Offline universal build; no core mod required')
p.add_argument('--minecraft-dir', type=Path, default=Path(r'D:\game\mcmod\1\.minecraft'))
p.add_argument('--jdk', type=Path, default=Path(r'C:\Users\ADMIN\.jdks\temurin-21'))
p.add_argument('--neoforge', default='21.1.249')
a = p.parse_args(); libs=a.minecraft_dir/'libraries'; best=None
for f in (a.minecraft_dir/'versions').glob('*/*.json'):
 try:
  data=json.loads(f.read_text(encoding='utf-8')); args=[x for x in data.get('arguments',{}).get('game',[]) if isinstance(x,str)]
  if '--fml.neoForgeVersion' not in args or args[args.index('--fml.mcVersion')+1]!='1.21.1': continue
  if best is None or len(data.get('libraries',[]))>len(best[0].get('libraries',[])): best=(data,args)
 except (ValueError,IndexError,OSError,AttributeError): continue
if best is None: raise SystemExit('NeoForge 1.21.1 profile not found')
data,args=best; mc=args[args.index('--fml.mcVersion')+1]; form=args[args.index('--fml.neoFormVersion')+1]; neo=a.neoforge
cp=[libs/f'net/neoforged/neoforge/{neo}/neoforge-{neo}-client.jar',libs/f'net/minecraft/client/{mc}-{form}/client-{mc}-{form}-srg.jar',libs/f'net/neoforged/neoforge/{neo}/neoforge-{neo}-universal.jar']
for x in cp:
 if not x.is_file(): raise SystemExit(f'Missing platform jar: {x}')
for lib in data.get('libraries',[]):
 path=lib.get('downloads',{}).get('artifact',{}).get('path','')
 if path and not path.startswith('net/neoforged/neoforge/') and (libs/path).is_file(): cp.append(libs/path)
resources=ROOT/'src/main/resources'; metadata=tomllib.loads((resources/'META-INF/neoforge.mods.toml').read_text(encoding='utf-8')); version=metadata['mods'][0]['version']; declared=re.search(r'(?m)^version\s*=\s*(\S+)',(ROOT/'version.properties').read_text(encoding='utf-8-sig')).group(1)
if version!=declared: raise SystemExit('Version mismatch')
out=ROOT/'build/classes-universal'; shutil.rmtree(out,ignore_errors=True);out.mkdir(parents=True); sources=sorted((ROOT/'src/main/java').rglob('*.java')); quote=lambda s:'"'+str(s).replace('\\','/')+'"'; argfile=ROOT/'build/universal.args';argfile.write_text('\n'.join(['-source','21','-target','21','-encoding','UTF-8','-proc:none','-d',quote(out),'-cp',quote(';'.join(map(str,cp))),*map(quote,sources)]),encoding='utf-8')
subprocess.run([str(a.jdk/'bin/javac.exe'),'@'+str(argfile)],check=True)
jar=ROOT/'build/libs'/f'daotu-{version}.jar';jar.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(jar,'w',zipfile.ZIP_DEFLATED) as z:
 for tree in (out,resources):
  for f in sorted(tree.rglob('*')):
   if f.is_file():
    if f.suffix=='.json': json.loads(f.read_text(encoding='utf-8-sig'))
    z.write(f,f.relative_to(tree).as_posix())
print(f'PASS {len(sources)} sources; {jar}; SHA256 {hashlib.sha256(jar.read_bytes()).hexdigest()}')

