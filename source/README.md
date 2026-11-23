# 傅利叶 FDH-6 简化网格的源文件（GPL-3.0）

本站的 `other_hands_mesh/fourier_fdh6.mjs` 由傅利叶 FDH-6 的模型简化而来。模型按 GPL-3.0 发布（全文见 [../LICENSES/fourier_fdh6-GPL-3.0.txt](../LICENSES/fourier_fdh6-GPL-3.0.txt)），所以这里附上生成它的全部源文件：

- `other_hands/fourier_fdh6/`：傅利叶在 [FFTAI/Wiki-GRx-Models](https://github.com/FFTAI/Wiki-GRx-Models/tree/7d96c758f048fe1bf92b3258864d94771ae0c093/Dexterous_hand/fourier_hand_6dof)（提交 7d96c75）里公开的 URDF、网格和许可证，原样没改；
- `other_hands/manifest.json`：这些文件在原仓库里的路径和 SHA-256；
- `make_other_hands.py`、`make_unitree_ends.py`：读 URDF、焊接顶点、边折叠简化、打包成模块的脚本，只用 Python 3 标准库，在这里按 GPL-3.0 提供。

在本目录运行下面的命令，生成的模块和本站那份逐字节相同：

```
python3 make_other_hands.py fourier_fdh6      # 写 other_hands_mesh/fourier_fdh6.mjs
```

脚本里列着本站所有灵巧手的参数，但这里只附了上面这一款的原文件，所以只能生成这一款。
