# Known differences and limits

The verified stamped CoD:UO image has **zero differing, added or missing bytes** compared with the original
2004-08-19 `flare.exe`: **573,440 bytes**, SHA-256 `eb395381133437b24db864c32d9af51f19d9d530df74b25350eff4bca17eaa46`.
All **1,275 project functions** pass complete-body byte and relocation checks; third-party/library code is counted separately.
The manifest's 119 translation units link normally without forced unresolved or duplicate symbols.

## Metadata that changes with each link

The ordinary linked image receives a fresh link timestamp and CodeView identity.
`--identical` keeps that ordinary image and writes a separate `flare_identical.exe` with the recorded values:

| Field | Original value |
| --- | --- |
| COFF and debug timestamp | 1092890739 / `0x41243073` (2004-08-19) |
| RSDS GUID bytes | `261732fa5086e24dbf1f57eadb393758` |
| GUID notation | `FA321726-8650-4DE2-BF1F-57EADB393758` |
| PDB age | 10 |

The original PDB path, `c:\Projects\Cod\bin\flare.pdb`, is supplied to the linker as an embedded string.
The stamp changes only the timestamp and RSDS GUID/age. Headers, sections, instructions, constants, initialized data,
imports, padding and the Rich table otherwise come from ordinary compilation and linking.

## Repeat the comparison

```text
python -I build/build.py --vc7 <Vc7> --sdk <uo-sdk> --jobs 1 --strict --identical --original <original-exe>
python -I build/stamp_meta.py check --input <built-exe> --original <original-exe>
```

Require the full hash above and `RESULT: IDENTICAL to the original flare.exe`.
The driver's successful exit status alone does not establish equality. The second command compares metadata only.
Neither command executes the resulting program. See [build instructions](../build/README.md).

## Source-level limits

Image identity does not recover exact local names, class keys, helper spelling, file names or header organization.
Equivalent source expressions can generate the same bytes. Record layouts can be constrained by accesses without revealing
every member's original type or purpose. Descriptive names and organization are explained in
[Reconstruction notes](RECONSTRUCTION_NOTES.md) and [Inferred names](INFERRED_NAMES.md).

Source readability and necessity review are separate from binary verification. The UO audit covers all 60 project translation units;
the CoD1 audit is lineage evidence and is not substituted for UO minimal-pair measurements.
The source contains no volatile qualifiers. A serialized-data member binding in the surface reader and an ordinary
size-field pointer in temporary-memory release preserve the measured address and load ordering; their original spelling remains unknown.
No runtime testing or correction of original defects is claimed.

## Retained sunlight boundary limitation

The sunlight plane buffer has 17 entries: one sky plane and room for at most 16 side planes.
`SunLight::SelectFace` rejects polygons only above 17 points, then builds one plane per point plus the sky plane.
A 17-point polygon therefore needs 18 entries. No sufficient caller invariant excluding that case is established here.
The reconstructed source preserves the original guard and storage. A behavior correction would change the reference image
and belongs in a separate nonmatching version.
