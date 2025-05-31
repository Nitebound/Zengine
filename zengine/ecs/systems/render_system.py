import moderngl
import numpy as np

from zengine.ecs.systems.system    import System
from zengine.ecs.components         import Transform, MeshFilter, Material
from zengine.ecs.components.camera  import CameraComponent
from zengine.util.quaternion        import quat_to_mat4

def compute_model_matrix(tr: Transform) -> np.ndarray:
    T = np.eye(4, dtype='f4');  T[:3,3] = (tr.x, tr.y, tr.z)
    R = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype('f4')
    return T @ R @ S

class RenderSystem(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx        = ctx
        self.scene      = scene
        self._vao_cache = {}

        # One‐time GL state
        self.ctx.enable(moderngl.DEPTH_TEST)
      # disable back‐face culling so CCW-wound quads (like your MeshFactory.rectangle) actually draw
        self.ctx.disable(moderngl.CULL_FACE)
      # keep winding info in case you want to re-enable culling later
        self.ctx.front_face = 'ccw'
        self.ctx.cull_face = 'back'

    def on_update(self, dt):
        # no drawing here—everything happens in on_render
        pass

    def on_render(self, renderer):
        # (1) Engine has already cleared once in Engine.run()
        #     so we do not clear here.

        # (2) Fetch camera matrices
        cam_e  = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)
        proj   = cp_cam.projection_matrix
        view   = cp_cam.view_matrix

        # (3) Draw all entities with Transform + MeshFilter + Material
        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material):
            tr  = self.scene.entity_manager.get_component(eid, Transform)
            mf  = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog  = mat.shader.program

            # Core uniforms (must exist in every shader)
            prog['projection'].write(proj.astype('f4').tobytes())
            prog['view'].      write(view.astype('f4').tobytes())
            prog['model'].     write(model.astype('f4').tobytes())

            # Material flags & values (silently skip missing uniforms)
            for uname, val in {
                'useTexture':     mat.extra_uniforms.get('useTexture', False),
                'useLighting':    mat.extra_uniforms.get('useLighting', False),
                'baseColor':      mat.albedo,
                'lightDirection': mat.extra_uniforms.get('lightDirection', (0,1,0)),
                'ambientColor':   mat.extra_uniforms.get('ambientColor',   (0.1,0.1,0.1,1)),
            }.items():
                if uname in prog:
                    prog[uname].value = val

            # Bind textures by name
            for slot, (uniform_name, tex) in enumerate(mat.textures.items()):
                tex.use(location=slot)
                if uniform_name in prog:
                    prog[uniform_name].value = slot

            # Extra per‐material uniforms
            for uname, val in mat.extra_uniforms.items():
                if uname in prog:
                    prog[uname].value = val

            # Build or fetch a VAO for this MeshAsset+Program combo
            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [
                    (self.ctx.buffer(mf.asset.vertices.astype('f4').tobytes()), '3f', 'in_position')
                ]
                if mf.asset.normals is not None:
                    content.append((self.ctx.buffer(mf.asset.normals.astype('f4').tobytes()), '3f', 'in_normal'))
                if mf.asset.uvs     is not None:
                    content.append((self.ctx.buffer(mf.asset.uvs.astype('f4').tobytes()),     '2f', 'in_uv'))
                if getattr(mf.asset, 'joints', None) is not None:
                    content.append((self.ctx.buffer(mf.asset.joints.astype('i4').tobytes()),  '4i', 'in_joints'))
                if getattr(mf.asset, 'weights', None) is not None:
                    content.append((self.ctx.buffer(mf.asset.weights.astype('f4').tobytes()), '4f', 'in_weights'))

                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            # Finally draw!
            self._vao_cache[key].render()
