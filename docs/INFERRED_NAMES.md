# Inferred source names

This inventory distinguishes evidence about behavior and layout from evidence about spelling.
It describes the current UO source; it is not a claim that all original identifiers have been recovered.
Local names, parameter names and filenames are descriptive unless stronger evidence is recorded.
The UO source review covers all project translation units; historical spelling remains uncertain where stated.

| Names / area | Evidence and limit |
| --- | --- |
| `Light_Compile`, `Q3Map_ReadPortalFile`, `GL_CreateWindow` and similarly printed routine names | Executable diagnostic strings support the corresponding function names |
| Shared Quake-family APIs | Published Q3/RTCW/ET source supports names where implementation and UO behavior agree |
| Engine model and animation APIs | Related retail-build symbols support some public API names; UO types and behavior still require independent comparison |
| `Light`, `AreaLight`, `DirectionalLight`, `PointLight`, `AreaCellLight`, `SunLight`, `SpotLight` and adjusted/linear classes | Virtual-table structure and constructor behavior establish roles and hierarchy; class/method spelling is descriptive |
| `Vector3d`, `Plane`, `Bounds`, `Winding` and colour records | Accesses and operations constrain layout and semantics; class keys and original type names remain inferred |
| `ColorRGB`, `Color3f`, `colorrgb.h` | Colour storage and conversion behavior support the model; type names and header split are reconstruction choices |
| `FloatSqrt` | A local float square-root wrapper preserves observed emission placement; no original-name evidence is claimed |
| Options record and parser state | Options reads and writes establish record layout; related-build names are supporting evidence rather than recovered UO declarations |
| Preview state and unread storage | Positions and sizes constrain storage; neutral names do not establish its original purpose |
| Local aliases and source boundaries | These describe current organization; image identity does not recover original spelling. The model bounds conversions now use ordinary ascending order with consistent pointer aliases |
| Surface-reader serialized-data view and temporary-memory size pointer | The bindings name actual count-byte and header-size storage. Their measured address/load ordering is established; exact historical spelling and representation remain inferred |

See [Evidence](EVIDENCE.md) for the evidence hierarchy and [Reconstruction notes](RECONSTRUCTION_NOTES.md) for retained forms and limits.
