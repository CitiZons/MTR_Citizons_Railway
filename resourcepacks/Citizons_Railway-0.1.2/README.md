# Citizons Railway 0.1.2

适用 Minecraft 1.20.1 / Forge 47.4.18 / MTR 4.0.3，配套 MTR Railway Point Advanced 0.1.6。轨距 1.435 m，轨面高 0.26428 m，轨底高 0.099422 m，重复单元长 0.6 m。

## 安装与样式

复制本文件夹或版本 ZIP 到实例的 `resourcepacks` 并启用。Point Advanced 在客户端和服务器使用相同构建。可选样式：

- 有砟普通轨道。
- 有砟外护轨轨道。
- 有砟中央护轨轨道。
- 无砟有枕：连续混凝土底板与带凸肩的承接块。
- 无砟无枕：两条连续纵向混凝土支撑，中央不铺混凝土板。

道岔若锁定了其他轨型，在蓝图中改回自动或对应 Citizons 样式。只装资源包时显示静态资源模型；程序化道岔、支承和连续护轨端头由 Point Advanced 生成。

## 模型与适配

`assets/mtrsteamloco/rails/citizons_railway.json` 提供 MTR 样式入口，`assets/citizons_railway/rail_profiles` 中的描述声明钢轨、枕木、扣件、道床、LOD 及连续护轨角色。普通轨道与道岔复用截面、材质和逐顶点 UV。

配套 Mod 0.1.6 为三种道床共用扣件布局；普通扣件实际重叠时使用滑床，护轨共座替换对应普通扣件。V 尖端内部扣件省略、外部护轨侧保留；匹配节点的钢轨、护轨和道砟微缝由 Mod 补面。

默认 LOD 分界为 4 m / 12 m，可在 Mod 配置中调整。有砟普通单元高／中／低模型为 2216 / 1056 / 502 面，钢轨截面一致。OBJ 使用共享位置、UV、法线索引；Mod 仍按面构造运行时四边形，实际性能收益尚待实机对比。

模型材质图集包含钢轨侧面、磨耗面、端面、混凝土、扣件及道砟；OBJ 使用标准 V 坐标，样式保持 `flipV: true`。尺寸和分组细节见 [MODEL_NOTES.md](MODEL_NOTES.md)。

`VERSION` 为资源包版本来源，`pack_format: 15` 为 Minecraft 资源格式版本；生成器和打包脚本位于项目根目录。
