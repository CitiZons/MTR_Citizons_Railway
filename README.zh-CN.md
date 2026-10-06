# Citizons Railway

[English](README.en.md) | [简体中文](README.zh-CN.md)

Minecraft **1.20.1** / Forge **47.4.18** / [MTR](https://github.com/Minecraft-Transit-Railway/Minecraft-Transit-Railway) **4.0.3** 的实体轨道资源包。当前版本 **0.1.3**，配套 [MTR Railway Point Advanced](https://github.com/CitiZons/MTR_Railway_Point_Advanced) **0.1.7**。

## 安装

1. 将 [Citizons_Railway-0.1.3.zip](dist/Citizons_Railway-0.1.3.zip) 放入实例的 `resourcepacks` 并启用，也可使用 `resourcepacks/Citizons_Railway-0.1.3` 文件夹。兼容文件 `dist/Citizons_Railway.zip` 内容相同。
2. 客户端和服务器安装同一构建的 Point Advanced 0.1.7，移除旧版 JAR。
3. 在 MTR 中选择下表中的轨型。道岔若手动锁定了其他轨型，在蓝图中改回自动或对应 Citizons 样式。

## 轨型

| MTR 样式 | 结构 |
|---|---|
| Citizons 高仿真钢轨 有砟 1435mm | 中央下凹混凝土轨枕、弹条扣件、弧坡梯形道砟。 |
| Citizons 高仿真钢轨(外护轨) 有砟 1435mm | 两条内侧护轨及共用加强承座，端头向中心内收。 |
| Citizons 高仿真钢轨(中央护轨) 有砟 1435mm | 平顶轨枕、中央护轨、独立螺栓压板及保护端头。 |
| Citizons 高仿真钢轨 无砟 有枕 1435mm | 连续混凝土底板和带凸肩的独立承接块。 |
| Citizons 高仿真钢轨 无砟 无枕 1435mm | 两条连续纵向混凝土支撑，中央不铺水平混凝土板。 |

轨距 **1.435 m**，轨面高 **0.26428 m**，重复单元 **0.6 m**。道砟最大厚度 **0.35 m**；有枕底板厚度为 0.35 m，无枕混凝土条加厚至同一道床底部。钢轨截面和扣件由各样式共用。

道岔、滑床、岔心、护轨承座及端点接续由 Point Advanced 生成。0.1.7 中三种道床共用扣件布局，V 尖端仅省略内部扣件、保留外部护轨侧扣件，并补齐匹配的钢轨、护轨、道砟及混凝土道床接头中不超过 2 cm 的缝隙。只装资源包时显示 MTR 的资源模型，不具备这些程序化功能。

## 精度

配套 Mod 默认在 **4 m / 12 m** 切换高／中／低精度，可在 Mod 配置中调整。各样式每个 0.6 m 重复单元的模型面数如下：

| 样式 | 高精度 | 中精度 | 低精度 |
|---|---:|---:|---:|
| 有砟普通轨道 | 2216 | 476 | 288 |
| 有砟外护轨 | 1691 | 476 | 346 |
| 有砟中央护轨 | 2632 | 600 | 396 |
| 无砟有枕 | 1806 | 395 | 259 |
| 无砟无枕 | 1720 | 318 | 182 |

单独使用资源包时，MTR 使用样式入口的高精度模型。

中低精度减少扣件侧壁、底面及道床、轨枕的下部细分，保留钢轨截面、接头分组和材质图集；高精度模型不变。OBJ 共用位置、UV 和法线索引。Point Advanced 0.1.7 按完整 8 m 区块缓存普通轨道和支承，并按区块切换精度；转动视角不重建未变化的几何。

## 再生成与打包

源目录为 `resourcepacks/Citizons_Railway`；其中 `VERSION` 是发布版本来源，`pack_format: 15` 表示 Minecraft 资源格式。

```powershell
python -m pip install numpy Pillow
python generate_citizons_railway.py
python railway_resource_checks/validate.py
python package_release.py
```

打包生成带版本 ZIP、兼容 ZIP 和可直接安装的 `resourcepacks/Citizons_Railway-0.1.3` 文件夹。模型预览使用 `railway_resource_checks/render.py`。

模型尺寸、分组与材质说明见 [MODEL_NOTES.md](resourcepacks/Citizons_Railway/MODEL_NOTES.md)，版本变化见 [CHANGELOG.md](CHANGELOG.md)。

本项目主要由 ChatGPT 实现。
