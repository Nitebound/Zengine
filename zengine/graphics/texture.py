from moderngl_window.resources import textures


class Texture:
    def __init__(self, path):
        self.texture = textures.load(path)

    def use(self, location=0):
        self.texture.use(location=location)
