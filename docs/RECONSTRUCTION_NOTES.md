# Reconstruction notes: CoD:UO flare

This source rebuilds the Call of Duty: United Offensive light compiler dated 2004-08-19.
All 1,275 project functions reproduce their original bytes and relocation destinations. The full image is identical after
the recorded metadata stamp; see [Known differences](KNOWN_DIFFERENCES.md) and [Evidence](EVIDENCE.md).

## What the image establishes

Instruction bytes, constants, strings, access widths, member offsets, virtual tables, calling behavior and linked placement
constrain the implementation. Function checks also bind relocations to their intended functions and data.
The full-file comparison covers headers, imports, initialized storage, section layout and padding.
An equal image does not identify a unique source text or reveal names of locals and types that have no surviving symbol evidence.

## Relationship to the earlier tool

UO flare shares much of the earlier Call of Duty light compiler, rebuilt with VC7.1 and real engine/tool changes.
The earlier reconstruction is useful evidence, while the UO executable decides behavior and code generation for this release.
Examples include DDS image decoding, filesystem handling and skeletal-model loading changes.
An unchanged algorithm can still require different source context or compiler options under VC7.1.

## Names, types and organization

Names have different evidence levels: executable strings, related published source, symbols from related retail builds,
or a descriptive choice. [Inferred names](INFERRED_NAMES.md) separates these cases.
Light-class and geometry names describe observed behavior; matching virtual tables and layouts alone do not recover their spelling.
Accessed offsets and field widths support domain records but do not establish the purpose of unread storage.

The manifest preserves measured translation-unit boundaries, flags, definition order and link order.
Inline members live in per-class headers or directly in their consuming source files; the release contains no `.inl` files.
Definition and include positions affect emitted inline copies, constants and linked placement.
Equivalent headers, source names or class keys may reproduce the same image and remain inferred.

## Removed compiler-sensitive forms

The UO source review found ordinary exact alternatives for the model bounds conversions: ascending component order and
consistent `mins`, `maxs` and `offset` pointer aliases. Redundant outer radius-sum parentheses were removed too.
A corrected 256-case natural-source family produced sixteen exact variants; the selected complete translation unit passes.
An unused area-cell-light origin reference was deleted. Sixteen hand-unrolled DXT stores were replaced by an ordinary four-row loop.
The complete cleanup-batch image remains identical. Earlier claims that the unusual conversion order or row unrolling were necessary
are superseded by these final-context measurements.

Both volatile reads were also removed. Temporary-memory release uses an ordinary pointer to the header's actual size field.
The surface reader binds its serialized count-byte view through the strip record before accumulating its index count.
All functions and the complete image remain identical; the source now contains no volatile qualifiers.

## Retained forms and measured alternatives

The UO review uses full-translation-unit with/without controls and, for emission/data order, complete-image comparisons.
The following findings are bounded to that compiler, flags and source context. A failed alternative does not establish a unique
historical spelling or rule out all possible natural alternatives. The readability audit covers all 60 project translation units.

| Area | Retained choice, mechanism and measured alternatives |
| --- | --- |
| Shader includes | Moving the mid-file qcommon/mathlib/options includes to the top preserves all 17 bodies but changes 1,356 image bytes through header-inline emission order; the narrow colour header keeps those definitions out of the initial parser functions |
| `FloatSqrt` | A dedicated float wrapper remains after the shader filename comparator; direct `sqrtf` loses its body, while the CRT overload and an earlier helper definition each change 33 image bytes; its name is descriptive |
| `sunLightScale` | Its declaration stays beside its user; moving it to the top changes 146 image bytes by reordering readonly data and references |
| Skeleton hierarchy | The second-pass bone-matrix binding affects address/operand roles; direct access differs, while a pointer binding is also exact, so reference syntax is not uniquely required |
| Area-cell light | Mixed normal/plane access and a tangent value snapshot affect x87 ordering and alias lifetimes; all-direct, all-alias, no-plane-binding and tangent-reference controls differ |
| Surface cursor | During sizing, the strip record's `numVerts` member views serialized count bytes; allocation then replaces that view with the unpacked array. Direct/local, hoisted, post-read, offset and unused-store/direct-read alternatives differ. The transient member store emits no code; the binding and member read together preserve the target's base/index ordering. Repeated base loads alone do not establish the compiler mechanism or historical spelling |
| Temporary-memory header | An ordinary pointer to the real size field preserves a separate load before subtraction. Replacing it with direct member access folds the load into subtraction and shortens the function from 67 to 65 bytes. Int and const-int pointers formed before or after validation are also exact |
| Brush and trace recursion | Removing the recursive inlining directives, individually or together where applicable, changes the accepted functions; the normal recursive algorithms are retained |
| Model occluders | A member-slot reference, mixed loop-bound access and class-local lifetimes affect address sharing; direct, pointer-snapshot and uniform-alias controls differ |
| View frustum | Declare-then-assign vectors keep by-value temporaries and copies; direct initialization constructs in place and changes the frame/body |
| BSP writing | Unread polygon results, brush totals and geometry defaults still generate stores or tests under `/Od`; isolated declaration/initializer/call reductions differ |
| Light compilation | An overwritten overbright initializer and an unread lightmap-mask local survive `/Od`; removing either changes its function |
| Entity writing | Initial `length` assignment and an indexed scratch store affect allocation or survive compilation; their isolated deletions differ; the copy itself is an ordinary while loop |
| Memory and character helpers | Narrow byte-mask operations and an explicit space exclusion retain the observed operands/tail; plain integer-test and condition-removal controls differ |
| Point-light planes | A per-edge plane binding with a direct sign-bit update affects x87 dot-product roles; direct indexed access differs |
| DXT endpoints | Repeated second-endpoint reads preserve packed RGB565 loads and scheduling; a cached colour value changes the function and inlining callers; row traversal uses the ordinary loop |
| Trace list and filesystem traversal | A guarded named list head and explicit while-loop cursor advances retain observed control flow and allocation; simpler structured-loop controls differ |
| Hierarchy and animation records | Packed count/read views and a two-member animation-buffer header/stride record affect loads and address selection; direct count/read and scalar-layout controls differ |
| Split scoring | The inline `SplitCounts::Score` member evaluates the `abs` call before sibling operands; a plain expression changes both selectors' saved-register/temporary roles |
| Occlusion exits | Direct exits continue outer scans through multiple loop levels; structured break/test and flag/break controls retain extra tests under `/Od` and change the functions |
| Filtering scratch | A class-array block encloses actual world-point filtering; flattening that lifetime changes `/Od` frame grouping |

CoD1 measurements are not substituted for UO controls. The source's exact original header organization, names and historical
reason for unused storage remain uncertain even when the retained form is measured.

The review distinguishes those forms from genuine packed-buffer accesses, bytewise bone masks, allocation prefixes and
ordinary multilevel exits. No register declarations, dead address escapes, fabricated users or undocumented assembly were added.
The serialized-data binding and size-field pointer have bounded full-translation-unit necessity controls.
Those controls establish measured dependencies among the tested alternatives, without establishing unique historical source text.

## Libraries and notices

JPEG 6b, zlib 1.1.4 and Quake-family minizip are separate components; see
[Third-party notices](../THIRD_PARTY_NOTICES.md). Their original notices accompany the sources.
The JPEG memory-source adapter and allocator/type integration are local adaptations, not claims of an unchanged upstream distribution.
Microsoft tools, libraries and SDK headers are supplied separately and are excluded from this source release.

## Metadata and validation

The stamp policy records the original timestamp and RSDS GUID/age. It does not contain target code or data.
Code, data, imports and the Rich header come from the manifest's ordinary compile/link process.
The exact pinned tools and SDK library mix are described in [build/README.md](../build/README.md).
This is a static reproducible-build result; no native output is executed during verification.
Runtime validation, modern compiler compatibility and repairs to original defects are outside that result.
The original sunlight plane-buffer boundary limitation is preserved; see [Known differences](KNOWN_DIFFERENCES.md).

## Credits

- Reconstruction by Jane.
- Published by Rose.
- Thanks to Prawy (https://github.com/PrawyCoD1) for the idea for this project.
