import moderngl

class Shader:
    def __init__(self, ctx, vertex_path, fragment_path):
        # force UTF-8 decoding
        with open(vertex_path,  'r', encoding='utf-8') as f:
            vs = f.read()
        with open(fragment_path,'r', encoding='utf-8') as f:
            fs = f.read()

        # create & store the Program
        self.program = ctx.program(
            vertex_shader=   vs,
            fragment_shader= fs,
        )

    def __getitem__(self, name):
        """
        shader['myUniform'] → Uniform object
        """
        return self.program[name]
