# Building CoD:UO flare.exe

Rebuild the Call of Duty: United Offensive light compiler dated 2004-08-19 with Visual C++ 7.1.
Python 3's standard library is sufficient (verified with Python 3.11 on Windows).
The compiler and linker run during the build; the resulting program is never executed.
Neither the original executable nor Microsoft software is included.

## Status

All **1,275 of 1,275 project functions** reproduce the original bytes and relocation destinations.
The 119 translation units link normally with no unresolved or multiply defined symbols.
After the documented metadata stamp, the image is **573,440 bytes**, SHA-256
`eb395381133437b24db864c32d9af51f19d9d530df74b25350eff4bca17eaa46`. Library functions are tracked separately from the project count.

## Requirements

| Component | Required version / source |
| --- | --- |
| Compiler | `cl.exe` 13.10.3077, Visual C++ 7.1 / Visual Studio .NET 2003 |
| Linker and librarian | `link.exe` and `lib.exe` 7.10.3077 from the same installation |
| CRT | VC7.1 `libc.lib`, `libcmt.lib`, `oldnames.lib`; `/ML` except the `/MT` command-library object |
| Headers | VC7.1 C/C++ headers and August 2001 Platform SDK headers |
| Most import libraries | February 2003 Platform SDK / VS .NET 2003: OpenGL32, GLU32, WinMM and GDI32 |
| USER32 | July 2002 Platform SDK, import-library build 7.10.2067 |
| KERNEL32 | VC7.1 installation's `lib/kernel32.lib`, import-library build 7.10.2179 |
| Host | Windows, Python 3; no third-party Python packages |

The SDK directory passed to `--sdk` contains `include/` and `lib/`. Put the five SDK import libraries listed above in its `lib/`;
KERNEL32 resolves from the VC7.1 `lib/`. This particular mix reproduces the original import hints and Rich header.
An arbitrary newer SDK does not. `build/toolchain_manifest.json` records selected required file hashes and provenance.
`--strict` checks the tools, CRT and import libraries against those hashes.

## Build

Run from the repository root:

```bat
python -I build\build.py --vc7 "C:\Program Files\Microsoft Visual Studio .NET 2003\Vc7" --sdk "C:\path\to\uo-sdk" --jobs 1 --strict --identical
```

Supply your own licensed installation and SDK files. Automatic downloading of the UO toolchain is unavailable in this release.
The included `fetch_toolchain.py` checks an installation; it does not fetch the older CoD1 compiler.

```bat
python -I build\fetch_toolchain.py --verify-only --vc7 "C:\Program Files\Microsoft Visual Studio .NET 2003\Vc7" --sdk "C:\path\to\uo-sdk"
```

`--original C:\path\to\flare.exe` optionally reads your own executable for comparison, without running it.
All paths in `sources.json` are relative to the repository root; the scripts also work from other directories.

## Options and outputs

| Option | Meaning |
| --- | --- |
| `--vc7 DIR`, `--sdk DIR` | Compiler root and separate SDK root; SDK defaults to the compiler's `PlatformSDK/` |
| `--strict` | Reject a missing or differing pinned tool/library |
| `--identical` | Keep ordinary `flare.exe` and write a separate stamped `flare_identical.exe` |
| `--original FILE` | Read an original copy for byte/section diagnostics when the result differs |
| `--out DIR` | Build outputs, default `build/out/`; use a fresh directory for verification |
| `--jobs N` | Compiler processes, clamped to 1 or 2; use 1 when sharing compiler access |
| `--keep-going` | Continue compilation after a failed unit |
| `--link-only` | Reuse objects in the output directory; unsuitable after source/flag changes |
| `--dry-run` | Print commands without running tools; creates output directories/response files |
| `--clean` | Delete the output directory first, even with `--dry-run` |
| `--progress` | Diagnostic forced link; unresolved/duplicate symbols make the result invalid |
| `--wine [COMMAND]` | Experimental tool execution through Wine; untested |

Outputs include `obj/`, `lib/cmdlib.lib`, `flare.exe`, `flare_identical.exe`, `flare.map`, `flare.pdb` and `link.log`.
Compiler diagnostics are in `<out>/work/<object>/compile.log`. The batch wrapper forwards options and exit status.
There are no prebuilt executables in the release.

## Build inputs and link order

The manifest contains 119 translation units, their measured flags, object order, static-library membership and link options.
JPEG 6b and zlib are ordinary objects; the command support object is placed in `cmdlib.lib`.
Base flags include `/O2 /Ob1 /GF /Gy /Zi /ML /DWIN32 /DNDEBUG /D_CONSOLE`.
Measured variants include `/Ob2`, `/Od`, `/GS`, `/EHsc`, `/YX` and `/MT` where recorded.
All UO inter-function padding is `0xCC`; padding alone does not establish optimization settings.

The normal link uses `/INCREMENTAL:NO /DEBUG /SUBSYSTEM:CONSOLE /STACK:8388608,4096 /OPT:WIN98 /OPT:NOREF /OPT:NOICF`
and `/NODEFAULTLIB:LIBCMT`, with OpenGL32, GLU32, WinMM, KERNEL32, USER32, GDI32 and the command library.
`libc` and `oldnames` resolve from object directives. The embedded PDB path is `c:\Projects\Cod\bin\flare.pdb`;
it is an original image constant, not a build-output location. `/PDB` writes beneath `--out`.
Do not reorder objects, includes or definitions as a build repair: these can affect code and data placement.

## Metadata stamp and checking

`--identical` normalizes the COFF/debug timestamp to **1092890739** (`0x41243073`), RSDS GUID bytes to
`261732fa5086e24dbf1f57eadb393758`, and PDB age to **10**, as recorded in `meta_stamp.json`.
The GUID in conventional notation is `FA321726-8650-4DE2-BF1F-57EADB393758`.
No code, data, import, padding or Rich-header bytes are copied from the original or patched.

Require `RESULT: IDENTICAL to the original flare.exe` and the SHA-256 above. The driver returns build success even when
the printed hash differs, so check the result explicitly. With `--original`, a differing result also writes `diff_report.txt`.
The metadata-only `stamp_meta.py check` command is supplementary and likewise reports differences in its text.
See [Known differences](../docs/KNOWN_DIFFERENCES.md), [Evidence](../docs/EVIDENCE.md) and
[Reconstruction notes](../docs/RECONSTRUCTION_NOTES.md).

## Linux and macOS

The driver has an experimental Wine path and converts paths through `winepath` (with a `Z:` mapping fallback).
It has not been validated by the maintainers. Image identity is established for the Windows reference configuration.
No runtime testing, modern compiler compatibility or portability is implied by the static result.

## Layout

`build.py` / `build.bat` drive the build; `sources.json` fixes flags and link order;
`stamp_meta.py` / `meta_stamp.json` describe the metadata policy;
`fetch_toolchain.py` / `toolchain_manifest.json` verify the supplied Microsoft files.
The public `src/` tree contains 198 files in the include closure and two vendor notices, with no `.inl` files.
The original executable, private verification tooling and Microsoft files are excluded.
