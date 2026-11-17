# Citizons Railway 0.1.5

[English](README.en.md) | [简体中文](README.zh-CN.md)

适用 Minecraft 1.20.1 / Forge 47.4.18 / [MTR](https://github.com/Minecraft-Transit-Railway/Minecraft-Transit-Railway) 4.0.3，配套 [MTR Railway Point Advanced](https://github.com/CitiZons/MTR_Railway_Point_Advanced) **0.1.7+**。轨距 1.435 m，轨面高 0.26428 m，轨底高 0.099422 m，重复单元长 0.6 m。

## 安装

复制本文件夹或版本 ZIP 到实例的 `resourcepacks` 并启用。安装 Point Advanced **0.1.7 或更新版本**，客户端和服务器使用相同构建，并移除旧版 JAR。道岔若锁定了其他轨型，在蓝图中改回自动或对应 Citizons 样式。

## 轨型

| MTR 样式 | 结构 |
|---|---|
| Citizons 高仿真钢轨 有砟 1435mm（新）／(旧) | 中央下凹混凝土轨枕、弹条扣件、弧坡梯形道砟。 |
| Citizons 高仿真钢轨(外护轨) 有砟 1435mm（新）／(旧) | 两条内侧护轨及共用加强承座，端头向中心内收。 |
| Citizons 高仿真钢轨(中央护轨) 有砟 1435mm（新）／(旧) | 平顶轨枕、中央护轨、独立螺栓压板及保护端头。 |
| Citizons 高仿真钢轨 无砟 有枕 1435mm | 连续混凝土底板和带凸肩的独立承接块。 |
| Citizons 高仿真钢轨 无砟 无枕 1435mm | 两条连续纵向混凝土支撑，中央不铺水平混凝土板。 |

三种有砟轨道各提供 `（新）` 与 `(旧)` 两个 MTR 入口，共 8 个样式；两者几何相同，仅图集材质不同。道岔、滑床、岔心、护轨承座及端点接续由 Point Advanced 生成。三种道床共用扣件布局，V 尖端仅省略内部扣件、保留外部护轨侧扣件，并补齐不超过 2 cm 的钢轨、护轨、道砟及混凝土道床接头缝隙。只装资源包时显示 MTR 的静态资源模型，不具备这些程序化功能。

`assets/mtrsteamloco/rails/citizons_railway.json` 提供八个 MTR 样式入口，且都显式声明 `textureId`。`assets/citizons_railway/rail_profiles` 中的描述声明钢轨、枕木、扣件、道床、LOD 及连续护轨角色。`models/rail/new` 与 `models/rail/old` 下每个 OBJ 都声明自己的 `mtllib`，并把 `map_Kd` 解析到对应变体图集。

## 精度

配套 Mod 默认在 **4 m / 12 m** 切换高／中／低精度，可在 Mod 配置中调整。各样式每个 0.6 m 重复单元的模型面数如下：

| 样式 | 高精度 | 中精度 | 低精度 |
|---|---:|---:|---:|
| 有砟普通轨道 | 1528 | 376 | 240 |
| 有砟外护轨 | 1232 | 446 | 298 |
| 有砟中央护轨 | 1810 | 530 | 298 |
| 无砟有枕 | 1210 | 285 | 213 |
| 无砟无枕 | 1140 | 238 | 172 |

单独使用资源包时，MTR 使用样式入口的高精度模型。

有砟枕木三档均保留完整 120 mm 高度、侧面贴图和承轨座高度，中低精度只减少上表面分段；普通轨道及外护轨枕木保留 35.111 mm 中央下凹，中央护轨枕木保持平顶。中低精度使用专用简化扣件；无砟有枕和直接支承的截面简化，同时保留钢轨截面、端盖及材质图集。OBJ 共用位置、UV 和法线索引。Point Advanced 按完整 8 m 区块缓存普通轨道和支承，并按区块切换精度。

## 再生成与打包

`VERSION` 为资源包版本来源，`pack_format: 15` 为 Minecraft 资源格式版本；生成器和打包脚本位于项目根目录。模型材质图集包含钢轨侧面、磨耗面、端面、混凝土、扣件及道砟；OBJ 使用标准 V 坐标，样式保持 `flipV: true`。尺寸和分组细节见 [MODEL_NOTES.md](MODEL_NOTES.md)。

本项目主要由 ChatGPT 实现。
