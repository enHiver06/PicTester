from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io

app = Flask(__name__)
CORS(app)  # 允许跨域访问

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


def check_image_transparency(img):
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


def check_image(img_data, image_type):
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


@app.route('/')
def root():
    """API根路径，返回欢迎信息"""
    return jsonify({
        "message": "图片检测API",
        "version": "1.0.0",
        "endpoints": {
            "POST /check-image": "检测单张图片",
            "GET /": "查看API信息"
        }
    })


@app.route('/check-image', methods=['POST'])
def check_image_endpoint():
    """
    检测单张图片是否符合要求

    参数:
    - image: 图片文件（multipart/form-data）
    - image_type: 图片类型，可选值：生活照、证件照

    返回:
    - success: 是否通过检测
    - message: 检测结果消息
    - errors: 错误列表（如果有）
    - image_info: 图片信息
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "message": "缺少图片文件",
                "errors": ["请上传名为'image'的文件"]
            }), 400

        # 检查是否有图片类型参数
        image_type = request.form.get('image_type')
        if not image_type:
            return jsonify({
                "success": False,
                "message": "缺少图片类型参数",
                "errors": ["请提供'image_type'参数，可选值：生活照、证件照"]
            }), 400

        # 读取上传的图片
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "未选择文件",
                "errors": ["请选择要上传的图片文件"]
            }), 400

        # 读取图片数据
        img_data = file.read()
        if not img_data:
            return jsonify({
                "success": False,
                "message": "上传的文件为空",
                "errors": ["文件内容为空"]
            }), 400

        # 执行检测
        result = check_image(img_data, image_type)

        # 根据检测结果返回适当的状态码
        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "服务器错误",
            "errors": [f"错误详情: {str(e)}"]
        }), 500


# Vercel 需要这个
if __name__ == '__main__':
    app.run(debug=True)
