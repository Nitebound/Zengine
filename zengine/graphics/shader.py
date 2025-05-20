import moderngl


class Shader:
    def __init__(self, ctx, vertex_path, fragment_path):
        # force UTF-8 decoding
        with open(vertex_path,  'r', encoding='utf-8') as f:
            vertex_src = f.read()
        with open(fragment_path,'r', encoding='utf-8') as f:
            fragment_src = f.read()

        self.program = ctx.program(
            vertex_shader=   vertex_src,
            fragment_shader= fragment_src,
        )
