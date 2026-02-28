# 喂件资源修复说明

## 问题
从 Octopress 迁移到 Pelican 时，图片和代码文件缺失。

## 原因
Octopress 的文件结构：
- 图片：gh-pages 分支的 `images` 目录
- 代码文件：gh-pages 分支的 `downloads/code` 目录

Pelican 生成时只是转换了 Markdown 文件，没有复制这些静态资源。

## 解决方案

### 1. 从 gh-pages 分支提取资源

```bash
# 提取 images 目录
git archive gh-pages images | gzip > images.tar.gz
tar -xzf images.tar.gz

# 提取 downloads 目录
git archive --format tar gh-pages:downloads | tar -x -C .
```

### 2. 更新 pelicanconf.py

添加静态文件路径配置：

```python
STATIC_PATHS = ["images", "downloads", "theme/images", "theme/css"]
```

### 3. 手动复制到输出目录

```bash
cp -r images downloads output/
```

## 资源统计

### 图片资源 (images/)
- **文件数量**: 46 个
- **文件类型**: PNG (24个)、JPG (15个)、JPEG (5个)、其他 (2个)
- **总大小**: 约 20 MB

**主要分类**:
- **音乐相关**: BWV1004, BWV1007-1012, CBSO (J.S.Bach、大提琴演奏)
- **技术图表**: branch-predictor, cudaErrorCudartUnloading, mm-CUDA
- **游戏开发**: GridViewDemo, 各种 UI 截图
- **其他**: favicon, icons, backgrounds

### 代码文件 (downloads/code/)
- **文件数量**: 21 个
- **文件类型**: Shell, Python, Lua, C++, DOT, PATCH, TXT
- **总大小**: 约 11 MB

**主要分类**:
- **Shell 脚本**: auto-deploy.sh, computeConv.sh 等
- **Python 脚本**: find_texture.py 等
- **Lua 补丁**: UILabel.lua.patch, UIPushButton.lua.patch 等
- **C++ 源码**: lua-snapshot/ 目录
- **其他**: GPUencode.dot, cocos2dx-tags

## 访问路径

### 本地预览
```
/images/filename.png
/downloads/code/filename.sh
```

### 生产环境
```
http://yszheda.github.io/blog/images/filename.png
http://yszheda.github.io/blog/downloads/code/filename.sh
```

## 文章中的引用

### 图片引用格式
```markdown
![image](/images/listings.png)
![image](/images/branch-predictor/bimodal.png)
```

### 代码文件引用格式
```markdown
[Code: rnn-sample](/downloads/code/rnn/quantangshi-sample.json)
```

## 注意事项

1. **Pelican 自动复制**: 配置了 `STATIC_PATHS` 后，Pelican 会自动复制这些目录
2. **目录结构保持**: 保持原有子目录结构 (如 images/branch-predictor/)
3. **文件名大小写**: 保持原始文件名 (如 "BWV1004", "CBSO")
4. **Windows 文件权限**: .sh 文件在 Windows 上可能需要重新设置执行权限

## 后续维护

- 添加新图片：放入 `images/` 或 `images/subdir/`
- 添加代码文件：放入 `downloads/code/`
- 运行 `pelican content -s pelicanconf.py -o output`
- 新资源会自动复制到 `output/` 目录

## 故障排查

### 图片不显示
1. 检查 `images/` 目录是否存在文件
2. 检查文章中的路径是否正确 (`/images/xxx.png`)
3. 清缓存：`rm -rf output && pelican content -s pelicanconf.py -o output`

### 代码文件 404
1. 检查 `downloads/code/` 目录是否存在文件
2. 检查文章中的路径是否正确 (`/downloads/code/xxx.sh`)
3. 验证 Pelican 配置中的 STATIC_PATHS 是否包含 "downloads"
