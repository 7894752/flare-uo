#!/usr/bin/env python3
"""Build the Call of Duty: United Offensive light compiler with Visual C++ 7.1 (VS .NET 2003).

Uses Python 3's standard library and the sources.json manifest beside this script.
The build compiles and links the program; it never executes the resulting image.

Examples (run from the repository root):
    python -I build/build.py --vc7 <Vc7> --strict --identical
    python -I build/build.py --vc7 <Vc7> --identical --original <original-exe>

The Vc7 directory contains bin/cl.exe, include/, lib/ and PlatformSDK/.
--identical writes a separate copy with the recorded timestamp, PDB GUID and age.
The printed SHA-256 result determines whether that copy equals the original.
See build/README.md for prerequisites, outputs and diagnostic options.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
sys.dont_write_bytecode = True
import threading

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / 'sources.json'


def sibling_module(name):
    """Load a build helper by its location, including under python -I."""
    spec = importlib.util.spec_from_file_location('flare_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stamp_module():
    """Load the metadata helper without changing Python's import search path."""
    return sibling_module('stamp_meta')


# SHA-256 and size of the 2004-08-19 release. The executable is not distributed.
ORIGINAL_SHA256 = 'eb395381133437b24db864c32d9af51f19d9d530df74b25350eff4bca17eaa46'
ORIGINAL_SIZE = 573440

# Toolchain files the byte-exact result was verified with (VC 7.10.3077 / cl 13.10.3077). A mismatch is a
# warning (error with --strict): other builds will compile, but are not expected to give identical bytes.
EXPECTED = {'bin/cl.exe': '2ecf86a3edfd3deae498e08298e210e984537ce9e11759930561e43f40bd2515', 'bin/link.exe': '0d5f9712d0da843d787bf4ce4e678abc6b737940996706b2c86101eac9df3e3c', 'bin/lib.exe': '3892c55821f628961ebf177537fdb002f3423166ead89c3aa7bc2ea1419fe1eb', 'lib/libc.lib': '25f494ca0238ae308edeab90dfaaa8c616b12f804a2156b51b9fba50eb144af1', 'lib/libcmt.lib': '6e2b3742e58245de52149137f64281b73db1487a07a31e165fff269fbf9b2ee8', 'lib/oldnames.lib': 'ace6ebf2ef319936a64b7e1a27f508a2c03c4838908f12e790b6c198845cc6cb', 'lib/kernel32.lib': '4c6f8667c02e990c496b1054429e01f3d7d1160323ac46b7771013ceaa4cb389'}
EXPECTED_SDK = {'lib/opengl32.lib': '87c245bac5172894e4748d2bb40a16dbfe8ff68123d394c6d4f2d8c6c383aa05', 'lib/glu32.lib': '94ecef35f8103431e64c616906ab0b8f46d1ea277906429b0c09949974a1d2c5', 'lib/winmm.lib': 'fcee69d2bdcb20e77a88ad30fb73eeda4c08982ca8b3ba857313ec77a1000044', 'lib/user32.lib': '0e3b9285cbdc030fdd124c9f45fa522e9f8d2476bfc383c6d17257be56000de2', 'lib/gdi32.lib': '52afc34ebfb1ee7b699cf3f36da11b963db1a754a725437c48c4c1f082b5041b'}

CREATE_NO_WINDOW = (0x08000000 | 0x4000) if os.name == 'nt' else 0   # no window, BELOW_NORMAL priority (shared PC)
print_lock = threading.Lock()

# Optional Wine mode (experimental, untested by the maintainers): every tool runs as `wine tool.exe ...` and
# every path handed to a tool is converted to a Windows path (`winepath -w`, fallback: Z: drive mapping).
WINE = None        # list such as ['wine'] when active
DRY_RUN = False    # print the commands instead of running them
_wpath_cache = {}


def wpath(p):
    """Path as the tool must see it: unchanged on Windows, Windows-style under Wine."""
    p = str(p)
    if WINE is None:
        return p
    if p in _wpath_cache:
        return _wpath_cache[p]
    if len(p) > 1 and p[1] == ':' and p[0].isalpha():      # already a Windows path
        w = p
    elif DRY_RUN:
        w = 'Z:' + p.replace('/', chr(92))
    else:
        try:
            r = subprocess.run(['winepath', '-w', p], capture_output=True, timeout=60)
            w = r.stdout.decode('utf-8', 'replace').strip() if r.returncode == 0 else ''
        except OSError:
            w = ''
        if not w:
            w = 'Z:' + p.replace('/', chr(92))
    _wpath_cache[p] = w
    return w


def sub(base, name):
    """base/name, resolved case-insensitively (Platform SDK folders are `Include`/`Lib` in some installs)."""
    d = Path(base) / name
    if d.exists() or not Path(base).is_dir():
        return d
    for e in Path(base).iterdir():
        if e.name.lower() == name.lower():
            return e
    return d


def log(*a):
    """Write a complete progress message without interleaving compiler threads."""
    with print_lock:
        print(*a, flush=True)


def sha256(p):
    """Hash a file without loading it all into memory."""
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


FETCHED = HERE / 'toolchain' / 'vc7'    # optional local installation


def find_vc7(arg):
    """Find Vc7 from --vc7, VCINSTALLDIR or the local installation."""
    if DRY_RUN and arg:
        return Path(arg.strip('"').rstrip(chr(92) + '/'))
    cand = arg or os.environ.get('VCINSTALLDIR')
    if not cand and (FETCHED / 'bin' / 'cl.exe').is_file():
        cand = str(FETCHED)
    if not cand:
        raise SystemExit('Pass --vc7 <path to the Vc7 folder>, set VCINSTALLDIR, and supply the SDK with --sdk.')
    p = Path(cand.strip('"').rstrip('\\/'))
    for c in (p, p / 'Vc7'):
        if (c / 'bin' / 'cl.exe').is_file():
            return c.resolve()
    raise SystemExit('No bin\\cl.exe under %s. Pass --vc7 <Vc7> and supply the SDK with --sdk.' % p)


def tool_env(vc7):
    """Find compiler DLLs and discard environment overrides of the manifest."""
    env = os.environ.copy()
    for k in ('CL', '_CL_', 'LINK', '_LINK_', 'INCLUDE', 'LIB', 'LIBPATH'):
        env.pop(k, None)
    extra = [vc7 / 'bin']
    for rel in ('../Common7/IDE', '../Common7/Tools', '../Common7/Tools/bin'):  # mspdb70.dll lives in Common7\IDE
        d = (vc7 / rel).resolve()
        if d.is_dir():
            extra.append(d)
    if WINE is None:
        env['PATH'] = os.pathsep.join([str(d) for d in extra] + [env.get('PATH', '')])
    else:
        # Wine extends the Windows PATH of the prefix from WINEPATH (Windows paths, ';' separated)
        env['WINEPATH'] = ';'.join([wpath(d) for d in extra] + ([env['WINEPATH']] if env.get('WINEPATH') else []))
    return env


def run(cmd, cwd, env, timeout=600):
    """Run a build tool, or print its command in dry-run mode.

    cmd[0] is a native filesystem path; other arguments already use Windows paths.
    Wine receives a response file when its command line would be too long.
    """
    if WINE is not None:
        tool, args = cmd[0], list(cmd[1:])
        cmd = [*WINE, tool, *args]
        if sum(len(a) + 1 for a in cmd) > 1800:          # long command lines go through a response file
            rsp = Path(cwd) / ('cmd_%d.rsp' % (abs(hash(tuple(args))) % 10**8))
            if not DRY_RUN:
                rsp.write_text(chr(10).join('"' + a + '"' for a in args) + chr(10), encoding='ascii')
            cmd = [*WINE, tool, '@' + wpath(rsp)]
    if DRY_RUN:
        log('DRY-RUN (cwd %s): %s' % (cwd, ' '.join('"%s"' % a if ' ' in a else a for a in cmd)))
        return 0, ''
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    return r.returncode, (r.stdout + r.stderr).decode('mbcs' if os.name == 'nt' else 'utf-8', 'replace')


def compile_one(tu, flag_sets, vc7, sdk, out, env):
    """Compile one manifest entry with its own temporary files and log."""
    src = ROOT / tu['source']
    if not DRY_RUN and not src.is_file():
        return tu, 1, 'Missing source %s. Restore the source tree listed in sources.json.' % src
    stem = tu['obj'][:-4]
    work = out / 'work' / stem
    work.mkdir(parents=True, exist_ok=True)
    flags = flag_sets[tu['flags']]
    obj = out / 'obj' / tu['obj']
    # Same include search as the verified build: the TU's own directory, the source root, then the toolchain.
    cmd = [str(vc7 / 'bin' / 'cl.exe'), *flags, '/I' + wpath(src.parent), '/I' + wpath(ROOT / 'src'),
           '/I' + wpath(sub(vc7, 'include')), '/I' + wpath(sub(sdk, 'include')),
           '/Fo' + wpath(obj), '/Fd' + wpath(work / 'compiler.pdb')]
    e = dict(env)
    if '/YX' in flags:
        cmd.append('/Fp' + wpath(work / 'auto.pch'))   # private PCH per TU, deleted afterwards
        # VC7 /YX can hang with a long absolute TMP path. The tool runs in work,
        # so a relative temporary directory keeps its files there without that bug.
        e['TMP'] = e['TEMP'] = '.'
    else:
        e['TMP'] = e['TEMP'] = wpath(work)
    cmd.append(wpath(src))
    code, text = run(cmd, work, e)
    if DRY_RUN:
        return tu, 0, ''
    (work / 'compile.log').write_text(text, encoding='utf-8')
    for junk in ('auto.pch', 'compiler.pdb'):
        try:
            (work / junk).unlink()
        except OSError:
            pass
    return tu, code if obj.exists() else (code or 1), text


def compile_all(man, vc7, sdk, out, env, jobs, keep_going):
    """Compile the manifest with bounded concurrency; return failed source paths."""
    (out / 'obj').mkdir(parents=True, exist_ok=True)
    tus = man['translation_units']
    failed = []
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(compile_one, tu, man['compile_flag_sets'], vc7, sdk, out, env) for tu in tus]
        for f in concurrent.futures.as_completed(futs):
            tu, code, text = f.result()
            done += 1
            if code:
                failed.append(tu['source'])
                log('FAILED  [%d/%d] %s\n%s' % (done, len(tus), tu['source'], text))
                if not keep_going:
                    for g in futs:
                        g.cancel()
                    break
            else:
                log('compiled [%d/%d] %s (%s)' % (done, len(tus), tu['source'], tu['flags']))
    return failed


def link_all(man, vc7, sdk, out, env, pdbaltpath, objdir=None, force=False):
    """Create static libraries, link in manifest order and record symbol errors."""
    obj = Path(objdir) if objdir else out / 'obj'

    # cmdlib is a static library built with /MT; the other objects use /ML.
    # Library members follow reference order. JPEG and zlib remain plain objects
    # so their contributions stay in the manifest's explicit link order.
    libdir = out / 'lib'
    libdir.mkdir(parents=True, exist_ok=True)
    libpath = {}
    for name, members in man['static_libraries'].items():
        lib = libdir / (name + '.lib')
        if lib.exists():
            lib.unlink()
        code, text = run([str(vc7 / 'bin' / 'lib.exe'), '/NOLOGO', '/OUT:' + wpath(lib), *[wpath(obj / m) for m in members]],
                         libdir, env)
        if code:
            raise SystemExit('lib.exe failed for %s. Check the compiler logs and object files in %s:%s%s' %
                             (name, obj, chr(10), text))
        libpath['@' + name] = wpath(lib)

    flags = list(man['link_flags'])
    flags += ['/PDB:' + wpath(out / 'flare.pdb'), '/OUT:' + wpath(out / 'flare.exe'), '/MAP:' + wpath(out / 'flare.map'),
              '/LIBPATH:' + wpath(sub(vc7, 'lib')), '/LIBPATH:' + wpath(sub(sdk, 'lib'))]
    flags = [f for f in flags if not f.startswith('/PDBALTPATH:')]
    if pdbaltpath:
        flags.append('/PDBALTPATH:' + pdbaltpath)
    flags += ['/INCLUDE:' + s for s in man.get('link_include_roots', [])]
    if force:
        flags += ['/FORCE:UNRESOLVED', '/FORCE:MULTIPLE']   # diagnostic output, marked invalid below
    inputs = [wpath(obj / t['obj']) for t in man['translation_units'] if t['project'] == 'flare']
    libs = [libpath.get(l, l) for l in man['link_libraries']]
    rsp = out / 'flare.rsp'
    rsp.write_text('\n'.join('"' + a + '"' for a in flags + inputs + libs) + '\n', encoding='ascii')
    code, text = run([str(vc7 / 'bin' / 'link.exe'), '@' + wpath(rsp)], out, env)
    if DRY_RUN:
        return out / 'flare.exe'
    (out / 'link.log').write_text(text, encoding='utf-8')
    refs = {}
    for objname, a, b in re.findall(r'(\S+) : error LNK\d+: unresolved external symbol (?:".*?" \((\S+?)\)|(\S+))', text):
        refs.setdefault(a or b, set()).add(objname)
    unresolved = sorted(refs)
    (out / 'unresolved.txt').write_text(chr(10).join('%s <- %s' % (u, ', '.join(sorted(refs[u]))) for u in unresolved) + chr(10), encoding='utf-8')
    multiple = sorted(set(re.findall(r'(\S+) : (?:error|warning) LNK(?:2005|4006): (.*)', text)))
    (out / 'multiply_defined.txt').write_text(chr(10).join('%s: %s' % m for m in multiple) + chr(10), encoding='utf-8')
    if code and not (force and (out / 'flare.exe').is_file()):
        print(text[-6000:])
        raise SystemExit('link.exe failed (exit %d): %d unresolved external symbols. See %s, unresolved.txt and '
                         'multiply_defined.txt; check that all manifest sources and toolchain libraries are available.'
                         % (code, len(unresolved), out / 'link.log'))
    log('link: %d unresolved external symbols, %d multiply defined%s' % (len(unresolved), len(multiple), ' (forced)' if force else ''))
    marker = out / 'FORCED_LINK_NOT_A_VALID_BUILD.txt'
    if marker.exists():
        marker.unlink()
    if force and (unresolved or multiple):
        FORCED_PROBLEMS.append((len(unresolved), len(multiple)))
        stars = '*' * 78
        banner = (stars + chr(10) + 'WARNING: this image was linked with /FORCE (%d unresolved, %d multiply defined symbols).' + chr(10) +
                  'It is NOT a valid build of flare.exe. Do not run it or compare its hash.' + chr(10) + stars) % (len(unresolved), len(multiple))
        print(banner)
        marker.write_text(banner + chr(10), encoding='utf-8')
    return out / 'flare.exe'


FORCED_PROBLEMS = []   # unresolved/duplicate counts from diagnostic links


def pe_info(path):
    """Read PE sizes, entry point, timestamp and raw sections without loading code."""
    d = Path(path).read_bytes()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = pe + 24
    info = {'size': len(d), 'timestamp': struct.unpack_from('<I', d, pe + 8)[0], 'entry': struct.unpack_from('<I', d, opt + 16)[0],
            'image_size': struct.unpack_from('<I', d, opt + 56)[0], 'sections': {}}
    for i in range(nsec):
        o = opt + struct.unpack_from('<H', d, pe + 20)[0] + 40 * i
        name = d[o:o + 8].rstrip(b'\0').decode('latin1')
        vsize, vaddr, rsize, rptr = struct.unpack_from('<IIII', d, o + 8)
        info['sections'][name] = {'vsize': vsize, 'vaddr': vaddr, 'rawsize': rsize, 'data': d[rptr:rptr + rsize]}
    return info


def section_report(ours, original):
    """Compare whole-file bytes, section contents, layout and Rich object counts."""
    ours_bytes, original_bytes = Path(ours).read_bytes(), Path(original).read_bytes()
    common = min(len(ours_bytes), len(original_bytes))
    differing = sum(x != y for x, y in zip(ours_bytes, original_bytes))
    added = len(ours_bytes) - common
    missing = len(original_bytes) - common
    first = next((i for i, (x, y) in enumerate(zip(ours_bytes, original_bytes)) if x != y), None)
    if first is None and (added or missing):
        first = common
    a, b = pe_info(ours), pe_info(original)
    lines = ['file size    : ours %d, original %d (%+d)' % (a['size'], b['size'], a['size'] - b['size']),
             'file bytes   : %d differing in common part, %d added, %d missing; %d total%s' % (
                 differing, added, missing, differing + added + missing,
                 ' (first file offset 0x%X)' % first if first is not None else ''),
             'entry point  : ours 0x%X, original 0x%X' % (a['entry'], b['entry']),
             'image size   : ours 0x%X, original 0x%X' % (a['image_size'], b['image_size']),
             'timestamp    : ours 0x%X, original 0x%X (%s)' % (
                 a['timestamp'], b['timestamp'],
                 'equal' if a['timestamp'] == b['timestamp'] else 'metadata stamp available with --identical')]
    for name in sorted(set(a['sections']) | set(b['sections'])):
        x, y = a['sections'].get(name), b['sections'].get(name)
        if not x or not y:
            lines.append('%-8s only in %s' % (name, 'ours' if x else 'original'))
            continue
        n = min(len(x['data']), len(y['data']))
        diff = sum(1 for i in range(n) if x['data'][i] != y['data'][i]) if x['data'][:n] != y['data'][:n] else 0
        first = next((i for i in range(n) if x['data'][i] != y['data'][i]), None)
        lines.append('%-8s vsize ours 0x%X / orig 0x%X (%+d)   raw ours 0x%X / orig 0x%X   differing bytes in common part: %d%s' % (
            name, x['vsize'], y['vsize'], x['vsize'] - y['vsize'], x['rawsize'], y['rawsize'], diff,
            ('  first at +0x%X (VA 0x%X)' % (first, 0x400000 + y['vaddr'] + first)) if first is not None else ''))
    lines += rich_report(ours, original)
    return chr(10).join(lines)


RICH_NAMES = {1: 'import thunks', 15: 'alias objects', 90: 'linker', 93: 'import-library objects', 95: 'C objects (cl, 3077)', 96: 'C++ objects (cl, 3077)', 105: 'assembler objects'}


def rich_counts(path):
    """Group the Rich header's object counts by tool identifier."""
    stamp_meta = stamp_module()
    r = stamp_meta.parse_rich(Path(path).read_bytes())
    out = {}
    if r:
        for comp, count in r[3]:
            out[comp >> 16] = out.get(comp >> 16, 0) + count
    return out


def rich_report(ours, original):
    """Compare linked object counts, including CRT members and import thunks."""
    a, b = rich_counts(ours), rich_counts(original)
    lines = ['', 'Rich header object counts (ours / original / delta):']
    for pid in sorted(set(a) | set(b)):
        lines.append('  prod %-3d %-26s %5d / %5d / %+d' % (pid, RICH_NAMES.get(pid, '?'), a.get(pid, 0), b.get(pid, 0), a.get(pid, 0) - b.get(pid, 0)))
    return lines


def check_toolchain(vc7, sdk, strict):
    """Check pinned tool and library hashes; reject mismatches in strict mode."""
    bad = []
    for base, table in ((vc7, EXPECTED), (sdk, EXPECTED_SDK)):
        for rel, want in table.items():
            p = base / rel
            if not p.is_file():
                bad.append('missing  ' + str(p))
            elif sha256(p) != want:
                bad.append('differs  ' + str(p))
    if bad:
        log('WARNING: toolchain files differ from the verified VC7.1 (13.10.3077 / 7.10.3077) install:')
        for b in bad:
            log('   ' + b)
        if strict:
            raise SystemExit('--strict: toolchain mismatch. Use the verified VC7.1 files and UO SDK library mix.')
    else:
        log('toolchain: all verified files match')


def main():
    """Parse build options, compile, link and report the resulting file hash."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--vc7', metavar='DIR', help='Vc7 root containing bin/cl.exe (default: %%VCINSTALLDIR%%, then build/toolchain/vc7)')
    ap.add_argument('--sdk', metavar='DIR', help='Platform SDK root containing include/ and lib/ (default: <vc7>/PlatformSDK)')
    ap.add_argument('--out', metavar='DIR', default=str(HERE / 'out'), help='output directory (default: build/out)')
    ap.add_argument('--identical', action='store_true',
                    help='write a separate metadata-stamped flare_identical.exe (timestamp and RSDS GUID/age from meta_stamp.json); does not imply byte identity')
    ap.add_argument('--original', metavar='FILE', help='original flare.exe to compare by section if the output hash differs')
    ap.add_argument('--progress', action='store_true',
                    help='diagnostic only: allow unresolved/duplicate symbols with /FORCE; mark such output invalid')
    ap.add_argument('--fetch-toolchain', action='store_true',
                    help='request toolchain download (unavailable for UO) into build/toolchain first (see fetch_toolchain.py; needs 7-Zip)')
    ap.add_argument('--7z', dest='sevenzip', metavar='FILE', help='7-Zip executable for --fetch-toolchain')
    ap.add_argument('--keep-downloads', action='store_true', help='with --fetch-toolchain: keep the downloaded archives')
    ap.add_argument('--jobs', metavar='N', type=int, default=2, help='parallel compiler processes, clamped to 1..2 (default: 2)')
    ap.add_argument('--keep-going', action='store_true', help='continue after a failed compile')
    ap.add_argument('--strict', action='store_true', help='fail if toolchain file hashes differ from the verified install')
    ap.add_argument('--link-only', action='store_true', help='reuse existing <out>/obj files instead of compiling')
    ap.add_argument('--clean', action='store_true', help='delete the output directory first, including during a dry run')
    ap.add_argument('--wine', nargs='?', const='wine', default=None, metavar='WINE_CMD',
                    help='experimental, untested: run VC7 tools under Wine (default command: wine); '
                         'enabled automatically when not on Windows')
    ap.add_argument('--dry-run', action='store_true',
                    help='print tool commands without executing them; output directories and a link response file are still created')
    args = ap.parse_args()
    global WINE, DRY_RUN
    DRY_RUN = args.dry_run
    if args.wine is None and os.name != 'nt':
        args.wine = 'wine'
        log('Not running on Windows: using Wine to run the VC7 tools (experimental, untested; see build/README.md).')
    if args.wine is not None:
        import shlex
        WINE = shlex.split(args.wine)

    man = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if args.fetch_toolchain:
        if DRY_RUN:
            log('DRY-RUN: would request toolchain download (unavailable for UO) in', FETCHED.parent)
        else:
            fetch_toolchain = sibling_module('fetch_toolchain')
            fetch_args = (['--7z', args.sevenzip] if args.sevenzip else []) + (['--keep'] if args.keep_downloads else [])
            if fetch_toolchain.main(fetch_args):
                raise SystemExit('Toolchain fetch failed. Review the fetcher messages and retry, or pass --vc7 <Vc7>.')
        if not args.vc7:
            args.vc7 = str(FETCHED)
    vc7 = find_vc7(args.vc7)
    sdk = Path(args.sdk).resolve() if args.sdk else sub(vc7, 'PlatformSDK')
    if not DRY_RUN and (not sub(sdk, 'lib').is_dir() or not sub(sdk, 'include').is_dir()):
        raise SystemExit('Platform SDK include\\ and lib\\ not found under ' + str(sdk) + ' (use --sdk)')
    out = Path(args.out).resolve()
    if args.clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    log('VC7   :', vc7)
    log('SDK   :', sdk)
    log('output:', out)
    if not DRY_RUN:
        check_toolchain(vc7, sdk, args.strict)
    env = tool_env(vc7)

    if not args.link_only:
        failed = compile_all(man, vc7, sdk, out, env, max(1, min(args.jobs, 2)), args.keep_going)
        if failed:
            raise SystemExit('%d translation unit(s) failed: %s' % (len(failed), ', '.join(failed)))
    # This is the PDB path recorded in the original RSDS record, not an output
    # directory. /PDB writes the actual PDB beneath --out.
    exe = link_all(man, vc7, sdk, out, env, r'c:\Projects\Cod\bin\flare.pdb', force=args.progress)
    if DRY_RUN:
        log('dry run finished: no tool was executed')
        return 0
    result = exe
    log('linked', exe)
    if args.identical and FORCED_PROBLEMS:
        raise SystemExit('refusing --identical: the image was linked with /FORCE (%d unresolved, %d multiply defined); it is not a valid build'
                         % FORCED_PROBLEMS[0])
    if args.identical:
        stamp_meta = stamp_module()
        result = out / 'flare_identical.exe'
        result.write_bytes(stamp_meta.apply_policy(exe.read_bytes(),
                                                   json.loads((HERE / 'meta_stamp.json').read_text(encoding='utf-8'))))
        log('stamped', result)
    digest = sha256(result)
    log('')
    log('sha256  ', digest)
    log('original', ORIGINAL_SHA256, '(%d bytes; yours: %d bytes)' % (ORIGINAL_SIZE, result.stat().st_size))
    if digest == ORIGINAL_SHA256:
        log('RESULT: IDENTICAL to the original flare.exe')
        return 0
    log('RESULT: differs from the original flare.exe (see build/README.md for comparison and toolchain checks)')
    if args.original:
        orig = Path(args.original)
        if sha256(orig) != ORIGINAL_SHA256:
            log('WARNING: --original is not the known flare.exe (sha256 %s)' % sha256(orig))
        rep_text = section_report(result, orig)
        (out / 'diff_report.txt').write_text(rep_text + chr(10), encoding='utf-8')
        log('')
        log(rep_text)
    else:
        log('Pass --original <path to your flare.exe> for byte counts, per-section differences and Rich-header counts.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
