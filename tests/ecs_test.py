from numpy import sqrt, vstack

from zengine.assets.mesh_registry import MeshRegistry
from zengine.core.engine import Engine
from zengine.core.scene  import Scene

from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light  import LightComponent, LightType
from zengine.ecs.components import Transform, MeshFilter, Material

from zengine.ecs.systems.input_system               import InputSystem
from zengine.ecs.systems.camera_system              import CameraSystem
from zengine.ecs.systems.player_controller_system   import PlayerControllerSystem
from zengine.ecs.systems.gltf_import_system         import GLTFImportSystem
from zengine.ecs.systems.animation_system           import AnimationSystem
from zengine.ecs.systems.skinning_system            import SkinningSystem
from zengine.ecs.systems.skinned_mesh_render_system import SkinnedMeshRenderSystem

class MyGame(Engine):
    def setup(self):
        scene = Scene()
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(scene.systems[0]))

        # ★ this now spawns **all** model entities for you ★
        scene.add_system(GLTFImportSystem(
            "assets/models/RiggedFigure.gltf",
            self.window.ctx,
            self.skinning_shader
        ))

        scene.add_system(AnimationSystem())
        scene.add_system(SkinningSystem())
        scene.add_system(SkinnedMeshRenderSystem())

        # 3) Camera
        # Camera setup (inside setup(), after you add CameraSystem)

        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0, y=-20, z=0))
        scene.entity_manager.add_component(cam,
                                           CameraComponent(
                                               aspect=self.window.width / self.window.height,
                                               projection=ProjectionType.PERSPECTIVE
                                           )
                                           )


        # # 3a Auto-center
        # all_verts = []
        # for mesh_key in MeshRegistry._meshes:
        #     verts = MeshRegistry.get(mesh_key).vertices
        #     all_verts.append(verts)
        #
        # if all_verts:
        #     verts = vstack(all_verts)  # (N,3)
        #     min_v = verts.min(axis=0)
        #     max_v = verts.max(axis=0)
        #     center = (min_v + max_v) * 0.5
        #     # approximate radius as half the diagonal
        #     radius = sqrt(((max_v - min_v) ** 2).sum()) * 0.5
        #
        #     # Now reposition the camera to sit on +Z, looking at center
        #     cam = scene.active_camera
        #     tr = scene.entity_manager.get_component(cam, Transform)
        #     tr.x, tr.y = center[0], center[1]
        #     tr.z = center[2] + radius * 2.5  # 2.5× zoom‐out
        #     # zero‐out any rotation around Z so it points straight at –Z
        #     tr.rot_x = tr.rot_y = tr.rot_z = 0
        #
        #     # And widen your far clip so you don’t clip out the model:
        #     cam_comp = scene.entity_manager.get_component(cam, CameraComponent)
        #     cam_comp.p_far = max(cam_comp.p_far, radius * 10)
        #     cam_comp.p_near = min(cam_comp.p_near, radius * 0.1)

        # light
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(x=5,y=5,z=5))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT, color=(1,1,1), intensity=1.0
        ))

        mesh_keys = list(MeshRegistry._meshes.keys())
        if mesh_keys:
            key = mesh_keys[0]
            mesh = MeshRegistry.get(key)

            debug_eid = scene.entity_manager.create_entity()
            # place it at the origin (feel free to move it later)
            scene.entity_manager.add_component(debug_eid, Transform(x=0, y=0, z=-10))
            scene.entity_manager.add_component(debug_eid, MeshFilter(mesh=mesh))
            scene.entity_manager.add_component(debug_eid,
                                               Material(
                                                   shader=self.default_shader,
                                                   albedo=(1.0, 0.2, 0.2, 1.0),
                                                   textures={}
                                               )
                                               )


        self.add_scene("main", scene, make_current=True)

if __name__ == "__main__":
    app = MyGame((1024,768), "ZEngine")
    app.setup()
    app.run()
