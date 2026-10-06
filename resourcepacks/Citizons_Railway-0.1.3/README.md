# Citizons Railway 0.1.3

[English](README.en.md) | [简体中文](README.zh-CN.md)

For Minecraft 1.20.1 / Forge 47.4.18 / [MTR](https://github.com/Minecraft-Transit-Railway/Minecraft-Transit-Railway) 4.0.3, paired with MTR Railway Point Advanced 0.1.7. Gauge: 1.435 m; rail-top height: 0.26428 m; rail-base height: 0.099422 m; repeat length: 0.6 m.

## Installation and styles

Copy this folder or the versioned ZIP to the instance's `resourcepacks` folder and enable it. Use the same Point Advanced build on the client and server. Available styles:

- Ballasted mainline.
- Ballasted outer guard.
- Ballasted central guard.
- Slab with sleepers: continuous concrete bed and separate shoulder support blocks.
- Direct support without sleepers: two longitudinal concrete strips with an open centre.

If a turnout is locked to another style, select automatic or the matching Citizons style in the blueprint. The pack alone provides static resource models; Point Advanced generates procedural turnouts, supports and continuous-guard terminals.

## Models and compatibility

`assets/mtrsteamloco/rails/citizons_railway.json` supplies the MTR style entries. Descriptors in `assets/citizons_railway/rail_profiles` identify rails, sleepers, fittings, beds, LODs and continuous guards. Ordinary rails and turnouts share sections, materials and per-vertex UVs.

Point Advanced 0.1.7 shares fitting placement across all three beds. Overlapping blade fittings use slide plates, and shared guard seats replace ordinary fittings. Inner V-nose fittings are omitted while outside guard fittings remain. The mod bridges matching gaps up to 2 cm in rails, guards, ballast and concrete beds.

Default LOD boundaries are 4 m / 12 m, configurable in the mod. A ballasted mainline unit has 2216 / 476 / 288 faces at high / medium / low detail, with matching rail sections. Medium and low detail reduce lower fitting, sleeper and bed geometry; high detail is unchanged. OBJ files share position, UV and normal indices. Point Advanced 0.1.7 caches ordinary rails and supports in complete 8 m chunks.

The texture atlas contains rail sides, polished heads, ends, concrete, fasteners and ballast. OBJ files use standard V coordinates with `flipV: true`. See [MODEL_NOTES.md](MODEL_NOTES.md) for dimensions and groups.

`VERSION` is the resource-pack version source; `pack_format: 15` is the Minecraft resource format. The generator and packaging scripts are in the project root.

This project is primarily implemented with ChatGPT.
