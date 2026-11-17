# 更新记录 / Changelog

## 0.1.5 — 2026-11-17

- 三种有砟轨道新增 `（新）` 默认入口和 `(旧)` 兼容入口。默认入口使用更浅的道砟、混凝土和轨枕配色，旧入口保留较早的深色材质；两套共用几何，各自使用独立图集和 `textureId`。MTR 样式入口由 5 个增至 8 个。
- 图集扩展到 800×800，新增独立的 `sleeper_concrete` 区域。枕木改用专门的无缝混凝土纹理，混凝土加入多尺度颜色与烘焙 AO，道砟颗粒配色重调。
- 重做中、低精度扣件轮廓：中精度使用简化的压板、侧板和轨距挡板，低精度收敛为单块底板；外护轨和中央护轨也使用对应的低、中精度专用件。
- 简化无砟有枕和直接支承的中、低精度截面：减少承接块肩部和纵条分段，直接支承中低精度抬高条底，减少不可见侧面。
- 修复首次进入世界时有砟轨道大面积变紫或材质缺失：`models/rail/new`、`models/rail/old` 下的变体 OBJ 重新声明各自的 `mtllib`，使 MTR 从同目录 MTL 解析材质，而不是回退到不存在的 `models/rail/{new,old}/mat.png`。
- 修复有砟外护轨中、低精度扣件回退高精度：低精度外护轨压板写入 `fastener_left` / `fastener_right` 分组，`ProfileModel.read` 不再因缺少扣件组而丢弃整套中、低精度模型。
- 修复中央护轨端头同时绘制偏移和未偏移扣件：护轨扣件组同时列入 `modelGroups.supports` 与 `continuousGuard.supportGroups`；端头保护鼻也不再附加与收窄钢轨重叠的锚栓。
- 为全部 8 个样式入口补齐显式 `textureId`；此前 `citizons_direct_1435` 缺少该字段。
- 面数更新为：有砟普通 1528／376／240，外护轨 1232／446／298，中央护轨 1810／530／298，无砟有枕 1210／285／213，无砟无枕 1140／238／172。
- 资源包再生成、运行时契约审计和打包通过；版本目录与兼容 ZIP 同步生成。
- 支持 Point Advanced `0.1.7+`；本版与 `0.1.11` 完整验证。

- Split each ballasted family into a `（新）` default entry and an `(旧)` compatibility entry. The default uses the lighter ballast, concrete and sleeper palette; the legacy entry keeps the earlier dark materials. Both share geometry but use separate atlases and `textureId` values. The pack now exposes 8 MTR style entries instead of 5.
- Expand the atlas to 800×800 and add a dedicated `sleeper_concrete` region. Sleepers use a separate seamless concrete texture; concrete gains multi-scale colour and baked AO, and the ballast palette is retuned.
- Rework medium and low fitting outlines: medium detail uses simplified pressure plates, side plates and gauge stops; low detail collapses to a single base plate. Outer and central guards use matching dedicated medium/low fittings.
- Simplify slab and direct-support LOD sections: reduce shoulder and longitudinal-strip segments, and raise the direct-support strip bottom at medium and low detail to remove unseen faces.
- Fix purple or missing-material ballasted tracks on first load: variant OBJs under `models/rail/new` and `models/rail/old` now declare their own `mtllib`, so MTR resolves the material from the adjacent MTL instead of falling back to the nonexistent `models/rail/{new,old}/mat.png`.
- Fix mid/low outer-guard fasteners falling back to high detail: the low-detail outer clamp now writes `fastener_left` / `fastener_right`, so `ProfileModel.read` no longer drops the entire mid/low LOD set for a missing fastener group.
- Fix duplicate offset and unshifted fasteners at tapered central-guard ends: guard fitting groups are listed in both `modelGroups.supports` and `continuousGuard.supportGroups`; the protective nose also no longer carries anchor bolts that overlap the converging rails.
- Add an explicit `textureId` to all eight style entries; `citizons_direct_1435` was previously missing it.
- Update face counts to 1528/376/240 for ballasted mainline, 1232/446/298 for outer guard, 1810/530/298 for central guard, 1210/285/213 for slab and 1140/238/172 for direct support.
- Regeneration, runtime-contract audit and packaging pass; the versioned folder and compatibility ZIP are rebuilt.
- Support Point Advanced `0.1.7+`; this release is fully validated with `0.1.11`.

## 0.1.4 — 2026-10-18

- 支持 Point Advanced 0.1.7 及更新版本；客户端与服务器需使用同一构建。
- Support Point Advanced 0.1.7 and later; use the same build on client and server.

- 有砟枕木三档恢复完整 120 mm 高度、中央下凹和侧面混凝土贴图，中低精度保留较少的上表面分段。
- 精简高精度扣件的圆柱细分与共面三角面，保留 W 形弹条、螺母、压板和底板轮廓。
- 适度精简高精度道砟坡肩，中低精度减少坡肩和纵向起伏细分；各档共享端部截面。
- 有砟普通轨道高／中／低精度为 1528／456／250 面；钢轨截面和端盖保持不变。

- Restore the full 120 mm body, central depression and textured sides of ballasted sleepers at every LOD, with fewer top-profile segments at medium and low detail.
- Reduce high-detail fitting cylinder subdivisions and merge coplanar cap triangles while retaining W clips, nuts, pressure plates and bases.
- Reduce ballast shoulder subdivisions, with lighter simplification at high detail and fewer longitudinal ripple segments at lower LODs; retain shared endpoint sections.
- Ballasted mainline high/medium/low detail uses 1528/456/250 faces per unit; rail sections and end caps are unchanged.

## 0.1.3 — 2026-10-06

相对 0.1.2：

- 简化五种轨型的中、低精度扣件、轨枕及道床几何，高精度模型保持不变。
- 有砟普通轨道中／低精度由 1056／502 面降至 476／288 面；两种护轨和无砟样式同样减少面数。
- 保留钢轨截面、接缝分组、轨距、轨面高度、0.6 m 重复长度及原材质图集。
- 配套 Point Advanced 0.1.7 的完整区块缓存与支承批处理，更新中英文安装、精度和模型说明。

Changes from 0.1.2:

- Simplify medium- and low-detail fittings, sleepers and beds across all five styles; high-detail models remain unchanged.
- Reduce ballasted mainline medium/low detail from 1056/502 to 476/288 faces per unit, with corresponding reductions in guard and slab styles.
- Retain rail sections, joint groups, gauge, rail-top height, the 0.6 m repeat length and the existing texture atlas.
- Pair with Point Advanced 0.1.7's complete-chunk cache and support batching; update English and Chinese installation, LOD and model documentation.

## 0.1.2 — 2026-10-05

相对 0.1.1：

- 新增无砟有枕轨道：连续混凝土底板、带凸肩和凹承轨座的独立承接块，底板厚度为 0.35 m。
- 新增无砟无枕轨道：两条无倒角的连续混凝土条，中心不变、宽度为初始设计的 1.8 倍，顶部接触扣件底座，底部加厚至道床底部；护轨处支撑加宽。
- 有枕承接块凸肩的纵向长度与扣件一致；无枕护轨支撑沿用同一混凝土材质和高度。
- 有砟样式名称统一加入“有砟”，补充两种无砟样式的轨型描述和 LOD，配套 Point Advanced 0.1.6。
- 简化低精度扣件的倒角、压板剖面和重复面；高精度去除螺纹细分及内部封闭重叠面，降低 W 形弹条的中间采样密度，保留路径锚点和半径。
- 恢复中央护轨扣件底板外露顶面，修复缺面。
- OBJ 改为共享位置、UV 和法线索引，减少文件与解析阶段的重复记录。

## 0.1.1 - 2026-09-30

- 新增外护轨、中央护轨两种样式，普通轨道模型保持不变。
- 外护轨位置、钢轨材质及共用承座按 Point Advanced 道岔实现对齐；修复支架悬空和内侧重复弹条。
- 中央护轨使用平顶轨枕和独立承座；两种端头均作为独立资源，避免每个重复单元出现内收分叉。
- 新的 continuousGuard 配置需 Point Advanced 0.1.4 或更新版本，提供真实端点、相邻接续和普通道岔模板。
- 提供带版本号的 ZIP 和可直接安装的解压资源包文件夹。

## 0.1.0 - 2026-09-28

首次资源包正式版本。`pack_format: 15` 继续表示 Minecraft 1.20.1 资源格式，与发布编号独立。

- 更新仓库和包内安装说明，区分资源包内容与客户端程序生成的道岔支撑。
- 补充配套 Point Advanced `0.1.3` 的平顶岔枕、尖轨滑床板、岔心底板及护轨／翼轨加强承座说明。
- 本轮不修改模型、贴图、轨距、轨面高度或道砟厚度。

包内 `VERSION` 是资源包编号来源；打包脚本同步资源包选择界面描述及 `Citizons_Railway-<版本>.zip` 文件名。保留 `dist/Citizons_Railway.zip` 作为同内容的兼容入口，供现有安装说明与 Mod 验证脚本使用。

现有资源：1435 mm 轨距、0.26428 m 轨面高度、0.35 m 最大道砟厚度、中央下凹混凝土轨枕、实体弹条及完整压板；三档模型共用钢轨截面。
