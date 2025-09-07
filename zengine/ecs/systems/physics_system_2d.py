from zengine.ecs.components import Transform
from zengine.ecs.systems.system import System
from zengine.ecs.components.physics.rigid_body_2d import RigidBody2D


class PhysicsSystem2D(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx = ctx
        self.scene = scene

    def on_update(self, dt):
        for obj in self.scene.entity_manager.get_entities_with(RigidBody2D):
            tf = self.scene.entity_manager.get_component(obj, Transform)
            rb = self.scene.entity_manager.get_component(obj, RigidBody2D)

            # tf.euler_z += .01
            tf.x += rb.velocity[0] * dt
            tf.y += rb.velocity[1] * dt
            tf.z += rb.velocity[2] * dt
            tf.euler_z += rb.angular_velocity[0] * dt
            tf.euler_x += rb.angular_velocity[1] * dt

            rb.velocity[0] *= .9994
            rb.velocity[1] *= .9994

            rb.angular_velocity[0] *= .999