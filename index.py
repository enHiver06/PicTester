from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from typing import Literal

app = FastAPI(
    title="图片检测API",
    description="检测图片格式、尺寸和透明度是否符合要求",
    version="1.0.0"
)

# 配置CORS，允许Dify等外部服务访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检测规则配置
RULES = {
    "生活照": {
        "format": "PNG",
        "size": (900, 1200),
        "transparent": True
    },
    "证件照": {
        "format": "PNG",
        "size": (400, 400),
        "transparent": True
    }
}


def check_image_transparency(img: Image.Image) -> tuple[bool, int]:
    """
    检查图片是否有足够的完全透明像素（alpha=0）
    要求：完全透明像素比例 > 0.1%
    返回: (是否透明, 完全透明像素数量)
    """
    try:
        # 转换为 RGBA 模式
        if img.mode == 'P':
            if 'transparency' in img.info:
                img = img.convert('RGBA')
            else:
                return False, 0

        if img.mode not in ('RGBA', 'LA'):
            return False, 0

        # 获取 Alpha 通道
        alpha = img.split()[-1]

        # 统计完全透明的像素（alpha = 0）
        alpha_data = list(alpha.getdata())
        fully_transparent_count = sum(1 for a in alpha_data if a == 0)

        # 计算总像素数
        total_pixels = img.width * img.height

        # 计算透明像素比例
        transparent_ratio = fully_transparent_count / total_pixels

        # 要求透明像素比例 > 0.1% (0.001)
        is_transparent = transparent_ratio > 0.001

        return is_transparent, fully_transparent_count

    except Exception as e:
        return False, 0


def check_image(img_data: bytes, image_type: str) -> dict:
    """
    检查图片是否符合要求
    返回: 检测结果字典
    """
    if image_type not in RULES:
        return {
            "success": False,
            "message": f"不支持的图片类型: {image_type}",
            "errors": [f"支持的类型: {', '.join(RULES.keys())}"]
        }

    rule = RULES[image_type]
    errors = []

    try:
        # 从二进制数据加载图片
        img = Image.open(io.BytesIO(img_data))

        # 检查格式
        if img.format != rule["format"]:
            errors.append(f"格式错误：当前为{img.format}，应为{rule['format']}")

        # 检查尺寸
        expected_size = rule["size"]
        if img.size != expected_size:
            errors.append(
                f"尺寸错误：当前为{img.width}×{img.height}，应为{expected_size[0]}×{expected_size[1]}"
            )

        # 检查透明度
        if rule["transparent"]:
            is_transparent, transparent_count = check_image_transparency(img)
            if not is_transparent:
                errors.append("透明度错误：非透明底（透明像素比例 < 0.1%）")

        # 返回结果
        if len(errors) == 0:
            return {
                "success": True,
                "message": "检测通过",
                "image_info": {
                    "format": img.format,
                    "size": f"{img.width}×{img.height}",
                    "mode": img.mode,
                    "transparent_pixels": transparent_count if rule["transparent"] else None
                }
            }
        else:
            return {
                "success": False,
                "message": "检测不通过",
                "errors": errors,
                "image_info": {
                    "format": img.format,
                    "size": f"{img.width}×{img.height}",
                    "mode": img.mode
                }
            }

    except Exception as e:
        return {
            "success": False,
            "message": "图片处理失败",
            "errors": [f"错误详情: {str(e)}"]
        }


@app.get("/")
async def root():
    """API根路径，返回欢迎信息"""
    return {
        "message": "图片检测API",
        "version": "1.0.0",
        "endpoints": {
            "POST /check-image": "检测单张图片",
            "GET /docs": "查看API文档"
        }
    }


@app.post("/check-image")
async def check_image_endpoint(
    image: UploadFile = File(..., description="要检测的图片文件"),
    image_type: Literal["生活照", "证件照"] = Form(..., description="图片类型")
):
    """
    检测单张图片是否符合要求

    参数:
    - image: 图片文件（支持PNG、JPG等格式）
    - image_type: 图片类型，可选值：生活照、证件照

    返回:
    - success: 是否通过检测
    - message: 检测结果消息
    - errors: 错误列表（如果有）
    - image_info: 图片信息
    """
    try:
        # 读取上传的图片数据
        img_data = await image.read()

        # 检查文件是否为空
        if not img_data:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        # 执行检测
        result = check_image(img_data, image_type)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# Vercel需要这个handler
handler = app
