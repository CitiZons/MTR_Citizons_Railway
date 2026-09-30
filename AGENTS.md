# 构建交付约定

- 每次构建完成后，必须把带版本号的发布包解压到 `D:\Minecraft\CitiZons\10.alpha\mods_edit\MTR_Citizons_Railway\resourcepacks\Citizons_Railway-<版本>`。
- 版本文件夹根目录必须包含 `pack.mcmeta` 和 `assets`；后续构建更新对应版本文件夹。仅生成 ZIP 不算完成交付。
- 标准流程：`python generate_citizons_railway.py`、`python railway_resource_checks/validate.py`、`python package_release.py`。生成器直接更新上述文件夹，打包时保留该文件夹。
