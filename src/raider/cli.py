from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import os
import time
import random

from typing import Tuple
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import load_config, save_config
from . import templates as tpl


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    eprint(">>", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def which_or_die(tool: str, name: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(f"Tool not found: {name} ('{tool}') is not in PATH.")
    return path


def project_root() -> Path:
    return Path.cwd()


def ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def render(template: str, **kw: Any) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace(f"@{k.upper()}@", str(v))
    return out


def collect_sources(root: Path, cfg: Dict[str, Any]) -> List[Path]:
    ex_dirs = set(cfg["format"]["exclude_dirs"])
    exts = set(cfg["format"]["extensions"])
    sources: List[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if p.suffix not in exts:
            continue
        if any(parent.name in ex_dirs for parent in p.parents):
            continue
        sources.append(p)
    return sources


def build_dir_for_preset(root: Path, preset: str) -> Path:
    return root / "build" / preset


def venv_bin_dir() -> Optional[Path]:
    prefix = Path(sys.prefix)
    for c in (prefix / "bin", prefix / "Scripts"):
        if c.exists() and c.is_dir():
            return c
    return None


def resolve_tool(name: str) -> Tuple[Optional[str], str]:
    vbin = venv_bin_dir()
    exts = [""] if os.name != "nt" else [".exe", ".bat", ".cmd", ""]

    if vbin:
        for ext in exts:
            cand = vbin / (name + ext)
            if cand.exists():
                return (str(cand), f"venv ({vbin})")

    found = shutil.which(name)
    if found:
        return (found, "PATH")

    return (None, "missing")


def tool_or_die(name: str, friendly: str) -> str:
    path, _where = resolve_tool(name)
    if not path:
        raise SystemExit(f"Tool not found: {friendly} ('{name}').")
    return path


# ---------------- Commands ----------------


def cmd_init(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)

    name = args.name or cfg["project"]["name"]
    cxxstd = args.cxxstd or cfg["project"]["cxx_standard"]

    cfg["project"]["name"] = name
    cfg["project"]["cxx_standard"] = int(cxxstd)

    ensure_dirs(root / cfg["paths"]["src_dir"], root / cfg["paths"]["tests_dir"])

    write_if_missing(root / "CMakePresets.json", tpl.TEMPL_PRESETS)
    write_if_missing(root / ".clangd", tpl.TEMPL_CLANGD)
    write_if_missing(root / ".clang-tidy", tpl.TEMPL_CLANG_TIDY)
    write_if_missing(root / ".clang-format", tpl.TEMPL_CLANG_FORMAT)

    write_if_missing(
        root / "CMakeLists.txt", render(tpl.TEMPL_CMAKELISTS, name=name, cxxstd=cxxstd)
    )
    write_if_missing(
        root / cfg["paths"]["src_dir"] / "main.cpp", render(tpl.TEMPL_MAIN, name=name)
    )
    write_if_missing(root / cfg["paths"]["tests_dir"] / "test_main.cpp", tpl.TEMPL_TEST)

    if cfg["deps"]["manager"] == "vcpkg":
        write_if_missing(
            root / cfg["deps"]["manifest"], render(tpl.TEMPL_VCPKG, name=name)
        )

    save_config(root, cfg)
    print("OK: init is done")


def cmd_configure(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    cmake = cfg["tools"]["cmake"]
    which_or_die(cmake, "cmake")

    preset = args.preset or cfg["presets"]["configure"]
    run([cmake, "--preset", preset], cwd=root)
    print("OK: config done!")


def cmd_build(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    cmake = cfg["tools"]["cmake"]
    which_or_die(cmake, "cmake")

    preset = args.preset or cfg["presets"]["build"]
    run([cmake, "--build", "--preset", preset], cwd=root)

    bdir = build_dir_for_preset(root, preset)
    cc = bdir / "compile_commands.json"
    if cc.exists():
        root_cc = root / "compile_commands.json"
        try:
            if root_cc.exists() or root_cc.is_symlink():
                root_cc.unlink()
            root_cc.symlink_to(cc)
            print("OK: symlink compile_commands.json at root.")
        except Exception:
            shutil.copy2(cc, root_cc)
            print("OK: compile_commands.json copied at root.")
    print("OK: build done!.")


def cmd_run(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)

    preset = args.preset or cfg["presets"]["build"]
    bdir = build_dir_for_preset(root, preset)

    # Optional: build first
    if args.build:
        cmake = tool_or_die(cfg["tools"]["cmake"], "cmake")
        run([cmake, "--build", "--preset", preset], cwd=root)

    # Determine target name
    target = args.target or cfg.get("run", {}).get("target") or cfg["project"]["name"]

    # Strip leading "--" if user used: raider run ... -- arg1 arg2
    prog_args = list(args.args)
    if prog_args and prog_args[0] == "--":
        prog_args = prog_args[1:]

    # Candidate executable locations
    candidates = [
        bdir / target,
        bdir / (target + ".exe"),
        bdir / "bin" / target,
        bdir / "bin" / (target + ".exe"),
    ]

    exe = None
    for c in candidates:
        if c.exists() and c.is_file():
            exe = c
            break

    # Fallback: pick newest runnable file in build dir
    if exe is None and bdir.exists():
        found = []
        for p in bdir.rglob("*"):
            if not p.is_file():
                continue
            if "CMakeFiles" in p.parts:
                continue
            if p.suffix.lower() in {
                ".a",
                ".so",
                ".dylib",
                ".lib",
                ".pdb",
                ".obj",
                ".o",
                ".cmake",
            }:
                continue

            if os.name == "nt":
                if p.suffix.lower() not in {".exe", ".bat", ".cmd"}:
                    continue
            else:
                if p.suffix != "":
                    continue
                if not os.access(p, os.X_OK):
                    continue

            found.append(p)

        if found:
            found.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            exe = found[0]

    if exe is None:
        raise SystemExit(
            f"Could not find executable '{target}' under {bdir}.\n"
            f"Try:\n"
            f"  raider build --preset {preset}\n"
            f"  raider run --preset {preset} --target <name>\n"
        )

    print(f">> running: {exe} {' '.join(prog_args)}")
    subprocess.run([str(exe), *prog_args], cwd=str(root), check=False)


def cmd_test(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    ctest = cfg["tools"]["ctest"]
    which_or_die(ctest, "ctest")

    preset = args.preset or cfg["presets"]["test"]
    run([ctest, "--preset", preset, "--output-on-failure"], cwd=root)
    print("OK: tests done!")


def cmd_fmt(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    clang_format = cfg["tools"]["clang_format"]
    which_or_die(clang_format, "clang-format")

    files = collect_sources(root, cfg)
    if not files:
        print("No file to format!")
        return

    for f in files:
        run([clang_format, "-i", str(f)], cwd=root)
    print(f"OK: {len(files)} file(s) formated.")


def cmd_tidy(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    clang_tidy = cfg["tools"]["clang_tidy"]
    which_or_die(clang_tidy, "clang-tidy")

    preset = args.preset or cfg["presets"]["build"]
    bdir = build_dir_for_preset(root, preset)
    cc = bdir / "compile_commands.json"
    if not cc.exists():
        raise SystemExit(
            f"compile_commands.json not found in {bdir}. Run: raider build --preset {preset}"
        )

    files = collect_sources(root, cfg)
    if not files:
        print("No file to analyze")
        return

    for f in files:
        run([clang_tidy, str(f), "-p", str(bdir)], cwd=root)
    print(f"OK: tidy check done in {len(files)} file(s).")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def cmd_deps_bootstrap(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)

    dest = (
        Path(args.dir)
        if args.dir
        else (root / cfg["deps"].get("vcpkg_root", ".tools/vcpkg"))
    )
    dest = dest.resolve()

    git = shutil.which("git")
    if not git:
        raise SystemExit("git not found in PATH (needed for vcpkg).")

    if dest.exists() and (dest / ".git").exists():
        print(f"vcpkg already in: {dest}")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(
            [git, "clone", "https://github.com/microsoft/vcpkg.git", str(dest)],
            cwd=root,
        )

    # Bootstrap (Windows vs Unix)
    if os.name == "nt":
        bootstrap = dest / "bootstrap-vcpkg.bat"
        if not bootstrap.exists():
            raise SystemExit("bootstrap-vcpkg.bat não encontrado.")
        run([str(bootstrap)], cwd=dest)
        vcpkg_exe = dest / "vcpkg.exe"
    else:
        bootstrap = dest / "bootstrap-vcpkg.sh"
        if not bootstrap.exists():
            raise SystemExit("bootstrap-vcpkg.sh não encontrado.")
        run(["bash", str(bootstrap)], cwd=dest)
        vcpkg_exe = dest / "vcpkg"

    if not vcpkg_exe.exists():
        raise SystemExit("Failed vcpkg exe generation.")

    cfg["deps"]["manager"] = "vcpkg"
    cfg["deps"]["vcpkg_root"] = str(dest)
    save_config(root, cfg)

    print(f"OK: vcpkg ready in {dest}")
    print(f"Tip: use the toolchain in CMake: {dest}/scripts/buildsystems/vcpkg.cmake")


def cmd_deps_add(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    if cfg["deps"]["manager"] != "vcpkg":
        raise SystemExit(
            "deps add/remove(WIP) only supports vcpkg manifest (vcpkg.json)."
        )

    manifest = root / cfg["deps"]["manifest"]
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}")

    data = read_json(manifest)
    deps = data.get("dependencies", [])
    if not isinstance(deps, list):
        raise SystemExit("invalid vcpkg.json: 'dependencies' needs to be a LIST")

    pkg = args.package.strip()
    if pkg in deps:
        print(f"Already exists: {pkg}")
        return
    deps.append(pkg)
    data["dependencies"] = deps
    write_json(manifest, data)
    print(f"OK: added '{pkg}' at {manifest}")


def cmd_deps_remove(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)
    if cfg["deps"]["manager"] != "vcpkg":
        raise SystemExit(
            "deps add/remove(WIP) only supports vcpkg manifest (vcpkg.json)."
        )

    manifest = root / cfg["deps"]["manifest"]
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}")

    data = read_json(manifest)
    deps = data.get("dependencies", [])
    if not isinstance(deps, list):
        raise SystemExit("invalid vcpkg.json: 'dependencies' needs to be a LIST.")

    pkg = args.package.strip()
    if pkg not in deps:
        print(f"Not found: {pkg}")
        return
    deps.remove(pkg)
    data["dependencies"] = deps
    write_json(manifest, data)
    print(f"OK: removed '{pkg}' in {manifest}")


def cmd_check(args: argparse.Namespace) -> None:
    root = project_root()
    cfg = load_config(root)

    checks = [
        ("cmake", "CMake"),
        ("ninja", "Ninja"),
        ("ctest", "CTest"),
        ("clang", "Clang (compiler)"),
        ("clangd", "clangd (LSP)"),
        ("clang-format", "clang-format"),
        ("clang-tidy", "clang-tidy"),
    ]

    ok_all = True
    print("Checking your consumables and enchants/gems...\n")
    for exe, desc in checks:
        path = resolve_tool(exe)
        if path:
            print(f"✅ {exe:<12} {desc:<20} -> {path}")
        else:
            ok_all = False
            print(f"❌ {exe:<12} {desc:<20} -> NOT FOUND")

    presets = root / "CMakePresets.json"
    cc = root / "compile_commands.json"
    print("\nFiles:")
    print(f" - {presets}: {'OK' if presets.exists() else 'missing'}")
    print(f" - {cc}: {'OK' if cc.exists() else 'missing'}")

    if not ok_all:
        raise SystemExit(1)


def cmd_raid_ready(args: argparse.Namespace) -> None:
    print("=== RAID READY CHECK ===")
    checks = [
        "Repair (100%)",
        "Talents/Spec correct",
        "UI/Addons loaded",
        "WeakAuras ok",
        "Logs/recording ok",
        "Enchants/Gems ok",
        "Rune + Flask + Food ok",
    ]
    for c in checks:
        print(f" - [X] {c}")
    print("\n✅ Type 'raider raid consumes' for consumables checklist.")


def cmd_raid_consumes(args: argparse.Namespace) -> None:
    print("=== CONSUMABLES CHECKLIST ===")
    items = [
        "Flask",
        "Food (feast/personal)",
        "Weapon oil / sharpening",
        "Augment rune",
        "Health potions",
        "Pre-pot",
        "Healthstone in bags",
        "Tomes",
        "Vantus rune",
    ]
    for it in items:
        print(f" - [X] {it}")
    print("\n💡 Tip: keep 2+ stacks of pots for prog nights.")


def cmd_raid_pull(args: argparse.Namespace) -> None:

    sec = int(args.seconds)
    if sec <= 0:
        print("Pull timer needs to be > 0.")
        return

    print(f"=== PULL IN {sec} ===")

    for t in range(sec, 0, -1):
        print(f"\x1b[2K\rPull in... {t}", end="", flush=True)
        time.sleep(1)

    print("\x1b[2K\rPULL NOW!      ")


def cmd_raid_meters(args: argparse.Namespace) -> None:

    if args.seed is not None:
        random.seed(args.seed)

    # Some fun names/specs (edit as you like)
    roster = [
        ("Atrocity", "Havoc DH"),
        ("Warnergold", "Havoc DH"),
        ("Paalas", "Havoc DH"),
        ("Selfmade", "Veng DH"),
        ("Threedose", "Fire Mage"),
        ("Imfiredup", "Fire Mage"),
        ("Sektant", "Arms War"),
        ("Ztey", "Balance Druid"),
        ("Littleholy", "Shadow Priest"),
        ("Maxshot", "BM Hunter"),
        ("Shuje", "Enh Shaman"),
        ("Mounir", "Enh Shaman"),
        ("Neeku", "Ret Pal"),
        ("Deepz", "Holy Pal"),
        ("Kleaver", "Fury War"),
        ("Aster", "Fury War"),
        ("Tomislav", "Fury War"),
        ("Sektant", "Fury War"),
        ("Lxks", "Brew Monk"),
        ("Arathy", "Sub Rogue"),
        ("Biscoitao", "Demo Lock"),
        ("Hikis", "Destro Lock"),
        ("Makuubara", "Frost DK"),
        ("Lilchking", "Blood DK"),
    ]

    width = max(10, int(args.width))

    # Pick 5 unique players
    picks = random.sample(roster, 5)

    # Make DPS numbers: "top" somewhere 180k-260k, others 60-220k
    base = random.randint(180_000, 260_000)
    dps_list = []
    for i, (name, spec) in enumerate(picks):
        # falloff per rank + some noise
        drop = i * random.randint(12_000, 28_000)
        noise = random.randint(-8_000, 10_000)
        dps = max(25_000, base - drop + noise)
        dps_list.append((name, spec, dps))

    # Sort highest first
    dps_list.sort(key=lambda x: x[2], reverse=True)

    top_dps = dps_list[0][2]

    # Fake fight metadata
    boss = random.choice(
        [
            "Patchwerk",
            "The Jailer",
            "C'Thun",
            "Sire Denathrius",
            "N’Zoth the Corruptor",
            "Gul’dan",
            "Argus the Unmaker",
            "G’huun",
            "Fyrakk the Blazing",
            "Sylvanas Windrunner",
            "Council of Blood",
        ]
    )
    duration = random.randint(240, 540)  # 4-9 min
    ts = time.strftime("%H:%M:%S")

    print(f"=== Details! Damage Done (Top 5) ===  [{ts}]")
    print(f"Fight: {boss}  |  Duration: {duration // 60}:{duration % 60:02d}")
    print("-" * (width + 38))

    # Render bars
    for rank, (name, spec, dps) in enumerate(dps_list, start=1):
        frac = dps / top_dps if top_dps else 0.0
        filled = int(round(frac * width))
        bar = "█" * filled + "░" * (width - filled)
        print(f"{rank:>2}. {name:<10} ({spec:<13})  {dps / 1000:>6.1f}k  {bar}")

    print("-" * (width + 38))
    print("Tip: blame priest for not giving PI")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="raider",
        description="Mythic raider CLI tool for C++/CMake/clang/nvim (WIP).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser(
        "init", help="Creates the project skeleton (CMake + Presets + clang tools)."
    )
    p_init.add_argument("--name", type=str, default=None)
    p_init.add_argument("--cxxstd", type=int, default=None)
    p_init.set_defaults(func=cmd_init)

    p_cfg = sub.add_parser("configure", help="cmake --preset <preset>")
    p_cfg.add_argument("--preset", type=str, default=None)
    p_cfg.set_defaults(func=cmd_configure)

    p_bld = sub.add_parser("build", help="cmake --build --preset <preset>")
    p_bld.add_argument("--preset", type=str, default=None)
    p_bld.set_defaults(func=cmd_build)

    p_run = sub.add_parser("run", help="Run the preset binary (dev/rel/etc)")
    p_run.add_argument("--preset", type=str, default=None, help="Preset (dev/rel/...)")
    p_run.add_argument(
        "--target",
        type=str,
        default=None,
        help="Executable name/target (default: config.run.target or project.name)",
    )
    p_run.add_argument("--build", action="store_true", help="Build before running")
    p_run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Args after '--' pass to program",
    )
    p_run.set_defaults(func=cmd_run)

    p_tst = sub.add_parser("test", help="ctest --preset <preset>")
    p_tst.add_argument("--preset", type=str, default=None)
    p_tst.set_defaults(func=cmd_test)

    p_fmt = sub.add_parser("fmt", help="clang-format -i in sources")
    p_fmt.set_defaults(func=cmd_fmt)

    p_tidy = sub.add_parser(
        "tidy", help="clang-tidy using compile_commands from preset"
    )
    p_tidy.add_argument("--preset", type=str, default=None)
    p_tidy.set_defaults(func=cmd_tidy)

    p_deps = sub.add_parser("deps", help="deps add/remove (WIP: vcpkg.json)")
    deps_sub = p_deps.add_subparsers(dest="deps_cmd", required=True)

    p_check = sub.add_parser(
        "check", help="Raid check tools and their paths (venv/PATH)."
    )
    p_check.set_defaults(func=cmd_check)

    p_boot = deps_sub.add_parser(
        "bootstrap", help="Clone and bootstrap vcpkg at .tools/vcpkg"
    )
    p_boot.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Destination dir (default: deps.vcpkg_root)",
    )
    p_boot.set_defaults(func=cmd_deps_bootstrap)

    p_add = deps_sub.add_parser("add", help="add pkg in vcpkg.json")
    p_add.add_argument("package", type=str)
    p_add.set_defaults(func=cmd_deps_add)

    p_rm = deps_sub.add_parser("remove", help="remove pkg from vcpkg.json")
    p_rm.add_argument("package", type=str)
    p_rm.set_defaults(func=cmd_deps_remove)

    p_raid = sub.add_parser("raid", help="Raid tools(ready check, consumables, etc.)")
    raid_sub = p_raid.add_subparsers(dest="raid_cmd", required=True)

    p_ready = raid_sub.add_parser("ready", help="Ready check (checklist local)")
    p_ready.set_defaults(func=cmd_raid_ready)

    p_cons = raid_sub.add_parser("consumes", help="Checklist de consumables")
    p_cons.set_defaults(func=cmd_raid_consumes)

    p_pull = raid_sub.add_parser("pull", help="Pull timer no terminal")
    p_pull.add_argument("seconds", type=int, nargs="?", default=10)
    p_pull.set_defaults(func=cmd_raid_pull)

    p_meters = raid_sub.add_parser("meters", help="Fake Details! top 5 DPS")
    p_meters.add_argument(
        "--seed", type=int, default=None, help="Seed for reproducible results"
    )
    p_meters.add_argument("--width", type=int, default=30, help="Bar width (chars)")
    p_meters.set_defaults(func=cmd_raid_meters)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)
