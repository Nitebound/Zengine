from PIL import Image
import moderngl

def load_texture_2d(ctx: moderngl.Context, path: str):
    img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM)
    texture = ctx.texture(img.size, 4, img.convert("RGBA").tobytes())
    texture.build_mipmaps()
    texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
    return texture
