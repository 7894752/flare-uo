# flare — Call of Duty: United Offensive Light Compiler (Byte-Identical Source)

Compiles with Visual C++ 7.1 to the exact bytes of the original 2004 `flare.exe`, with the metadata stamp described below.

A source reconstruction of `flare.exe`, the light compiler (lightmaps, light grid, model lighting, OpenGL preview) that shipped with the
2004 Call of Duty: United Offensive map tools. The source is written so that Microsoft Visual C++ 7.1 (Visual Studio .NET 2003) reproduces the original
machine code.

This project is not affiliated with or endorsed by Activision, Infinity Ward, id Software, ZeniMax or Microsoft. "Call of Duty", "Quake" and
"Wolfenstein" are trademarks of their respective owners and are used here only to describe what the code is. No game data, no original
binary and no Microsoft software is part of this repository.

## Status

- **1,275 of 1,275** project functions compile to the same bytes and relocations as the original, checked one by one.
- The program links normally. `--identical` writes a separate copy with the recorded link timestamp, PDB GUID and PDB age (10).
  That copy is **byte-identical** to the original: 573,440 bytes, SHA-256
  `eb395381133437b24db864c32d9af51f19d9d530df74b25350eff4bca17eaa46`. Code, data, imports, layout and the Rich header come
  from compilation and linking; the stamp changes only the three metadata fields. The ordinary linked image is retained.
- Byte identity proves the compiled image, not the source text: where several spellings compile to the same bytes, the choice among them
  is not evidence about the original. See [docs/RECONSTRUCTION_NOTES.md](docs/RECONSTRUCTION_NOTES.md).

Details: [docs/KNOWN_DIFFERENCES.md](docs/KNOWN_DIFFERENCES.md). Third-party and library functions are accounted for separately from the project count.

## Requirements

- Windows and Python 3 (verified with Python 3.11; standard library only).
- Visual C++ 7.1, `cl.exe` 13.10.3077 and `link.exe` / `lib.exe` 7.10.3077 (Visual Studio .NET 2003),
  the static CRT and the UO SDK library mix described in [build/README.md](build/README.md).
  Other compiler builds and SDK libraries do not give the same image.

## Build

With your installed, verified VC7.1 and SDK files:

```bat
python -I build\build.py --vc7 "C:\Program Files\Microsoft Visual Studio .NET 2003\Vc7" --sdk "C:\path\to\uo-sdk" --jobs 1 --strict --identical
```

The build compiles 119 translation units from a 200-file source/header/notice set, builds `cmdlib.lib` and links normally.
It prints the result's SHA-256 next to the recorded release hash and never runs the resulting program.
Add `--original C:\path\to\flare.exe` for byte and section diagnostics if the result differs.
The original executable is optional. The release does not download Microsoft files automatically;
see [build/README.md](build/README.md) for the exact SDK components, hashes, options and outputs.

## Binaries

This repository contains no executables. The program it rebuilds is the original `flare.exe` from the Call of Duty: United Offensive (2004) mod tools; if you
just need the tool, use the official mod tools.

## How the match is established

Each function is compiled with the original compiler and measured flags. Its instruction bytes, relocation targets, jump tables and
C++ exception-handling contributions must agree with the original. The complete linked image is then compared byte for byte, including
headers, data, imports and padding. The per-function checks used private tooling; the standalone build needs only the source in `src/`
and the manifest in `build/sources.json`.
Where several spellings give identical bytes, the choice among them is not evidence about the original source.

## Repository layout

```
src/        the reconstruction (flare/, common/, code/, libs/, universal/, win32/)
build/      build.py, build.bat, sources.json, fetch_toolchain.py, stamp_meta.py, meta_stamp.json, README.md
docs/       known differences, notes on what is proven and what is a choice
COPYING     GPLv3 with id Software's additional terms
THIRD_PARTY_NOTICES.md
```

## License

GPL-3.0-or-later with the additional terms id Software applied to its Wolfenstein source releases: see [COPYING](COPYING). Files that
descend from the Quake III Arena source keep their original headers (GPL version 2 or, at your option, any later version), which is used
here under version 3. Third-party code (IJG jpeg 6b, zlib, minizip) is under its own terms: see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This software is based in part on the work of the Independent JPEG Group.

## Credits

- Reconstruction by Jane.
- Published by Rose.
- Thanks to Prawy (https://github.com/PrawyCoD1) for the idea for this project.

Evidence and sources (details in [EVIDENCE.md](docs/EVIDENCE.md) and [INFERRED_NAMES.md](docs/INFERRED_NAMES.md)):

- id Software: Quake III Arena (`q3map`, `common`, `qcommon`) and the Return to Castle Wolfenstein and Wolfenstein:
  Enemy Territory source releases, the base of the engine family.
- The GtkRadiant and q3map2 authors, whose published tools show the same family of code.
- Independent JPEG Group (libjpeg 6b), Jean-loup Gailly and Mark Adler (zlib 1.1.4), Gilles Vollant (minizip).
- Function and variable names come from strings in the binary, the published sources above and the symbol tables and link maps of other
  retail builds of the same game family, wherever the compiled image agrees; the rest are descriptive.

## Ports

This repository is the byte-identical reference build and stays that way. Ports to x64, to modern compilers or to other
platforms are welcome as forks; the hope is that someone takes this on.
