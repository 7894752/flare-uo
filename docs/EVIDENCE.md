# Evidence and verification

The reference is the 2004-08-19 Call of Duty: United Offensive `flare.exe`.
[Known differences](KNOWN_DIFFERENCES.md) records its complete hash, size and metadata policy.
The original executable, Microsoft files and private verification data are not distributed.

## Evidence order

1. The UO executable: bytes, relocations, strings, constants, virtual tables and linked layout.
2. id Software's published [Quake III Arena](https://github.com/id-Software/Quake-III-Arena) source, including q3map and shared engine/tool code.
3. The related [RTCW single-player](https://github.com/id-Software/RTCW-SP), [RTCW multiplayer](https://github.com/id-Software/RTCW-MP)
   and [Enemy Territory](https://github.com/id-Software/Enemy-Territory) sources.
4. GtkRadiant/q3map2 for later algorithms and family conventions, checked against this executable.
5. Symbol tables and link maps from related retail builds for names and records, where UO behavior and layout agree.
6. Descriptive naming and implementation choices where stronger evidence is absent.

The earlier Call of Duty tool reconstruction provides additional lineage evidence. It is not original source and cannot settle
UO-specific differences or establish original spelling by itself.
The JPEG implementation follows the [IJG 6b distribution](https://ijg.org/files/jpegsrc.v6b.tar.gz);
compression follows [zlib 1.1.4](https://github.com/madler/zlib/tree/v1.1.4).
Minizip follows the Quake-family unzip 0.15 source with its retained notices.

## Static checks

All 1,275 project functions have complete-body byte and relocation checks under VC7.1, `cl.exe` 13.10.3077.
Each reference is bound to the intended function, object, string or constant; equality with an unbound relocation is insufficient.
Jump/index tables, alignment tails and C++ exception contributions are included where applicable.
Library bodies are accounted for separately, without adding to the project count.

The standalone build compiles the 119-unit manifest and links normally. After stamping the recorded timestamp and RSDS GUID/age,
the complete file equals the reference, including headers, sections, data, imports, padding and Rich header.
The original is optional for the build and is read only for comparison. No target bytes are used to supply missing code.
The build reports the expected hash and its actual result; a zero process exit alone does not establish equality.

## Repeating the image check

```text
python -I build/build.py --vc7 <Vc7> --sdk <uo-sdk> --jobs 1 --strict --identical --original <original-exe>
```

See [build/README.md](../build/README.md) for exact Microsoft components and outputs.
No runtime test coverage or unique historical source spelling is implied by the static proof.
UO source necessity/readability review remains separate; see [Reconstruction notes](RECONSTRUCTION_NOTES.md).
