import numpy as np
from zengine.ecs.components import Transform, SpriteRenderer

def compute_model_matrix(transform):
    translation = np.identity(4, dtype='f4')
    translation[0, 3] = transform.x
    translation[1, 3] = transform.y

    rotation = np.identity(4, dtype='f4')
    angle = np.radians(transform.rotation)
    rotation[0, 0] = np.cos(angle)
    rotation[0, 1] = -np.sin(angle)
    rotation[1, 0] = np.sin(angle)
    rotation[1, 1] = np.cos(angle)

    scale = np.identity(4, dtype='f4')
    scale[0, 0] = transform.scale_x
    scale[1, 1] = transform.scale_y

    model = translation @ rotation @ scale
    return model


import numpy as np
from zengine.ecs.components import Transform, SpriteRenderer

class RenderSystem:
    def process(self, renderer, camera, entity_manager):
        view_projection = camera.get_view_projection()

        for eid in entity_manager.get_entities_with(Transform, SpriteRenderer):
            transform = entity_manager.get_component(eid, Transform)
            sprite = entity_manager.get_component(eid, SpriteRenderer)

            model = self.compute_model_matrix(transform)
            renderer.draw_quad(model, view_projection)

    def compute_model_matrix(self, transform):
        translation = np.identity(4, dtype='f4')
        translation[0, 3] = transform.x
        translation[1, 3] = transform.y

        rotation = np.identity(4, dtype='f4')
        angle = np.radians(transform.rotation)
        rotation[0, 0] = np.cos(angle)
        rotation[0, 1] = -np.sin(angle)
        rotation[1, 0] = np.sin(angle)
        rotation[1, 1] = np.cos(angle)

        scale = np.identity(4, dtype='f4')
        scale[0, 0] = transform.scale_x
        scale[1, 1] = transform.scale_y

        return translation @ rotation @ scale
