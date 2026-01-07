# 图片检测API

这是一个基于FastAPI的图片检测服务，用于检测图片的格式、尺寸和透明度是否符合要求。

## 功能特性

- ✅ 支持生活照检测（900×1200，PNG，透明底）
- ✅ 支持证件照检测（400×400，PNG，透明底）
- ✅ 自动生成API文档
- ✅ 支持Vercel一键部署
- ✅ 可集成到Dify等AI平台

## 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
uvicorn api.index:app --reload --port 8000
```

3. 访问API文档：
打开浏览器访问 http://localhost:8000/docs

## API接口

### POST /check-image

检测单张图片是否符合要求。

**参数：**
- `image`: 图片文件（multipart/form-data）
- `image_type`: 图片类型，可选值：`生活照` 或 `证件照`

**返回示例：**
```json
{
  "success": true,
  "message": "检测通过",
  "image_info": {
    "format": "PNG",
    "size": "900×1200",
    "mode": "RGBA",
    "transparent_pixels": 12500
  }
}
```

## 部署到Vercel

1. 将代码推送到GitHub
2. 在Vercel中导入GitHub仓库
3. Vercel会自动检测并部署

## 集成到Dify

在Dify中配置自定义工具：
- API端点：`https://your-domain.vercel.app/check-image`
- 方法：POST
- 参数：image（文件）、image_type（文本）
