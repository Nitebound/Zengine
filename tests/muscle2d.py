# requirements:
# pip install pygame Box2D
# run: python muscle_rig_topdown.py

import math
import random
import pygame
from pygame.math import Vector2
from Box2D import (
    b2World, b2Vec2,
    b2PolygonShape, b2CircleShape, b2FixtureDef, b2BodyDef, b2_staticBody, b2_dynamicBody,
    b2RevoluteJointDef, b2DistanceJointDef, b2FrictionJointDef, b2ContactListener
)

# ------------------------------------------------------------
# Config / Controls
# ------------------------------------------------------------
PPM = 60.0
DT = 1.0 / 60.0
VEL_ITERS = 16
POS_ITERS = 6
SCREEN_W, SCREEN_H = 1100, 700
BG = (16, 17, 20)
COL_TORSO = (90, 180, 255)
COL_BONE = (230, 230, 230)
COL_HAND = (255, 215, 64)
COL_MUSCLE_IDLE = (255, 90, 90)
COL_MUSCLE_ACTIVE = (255, 0, 0)
COL_ENEMY = (150, 255, 150)

# Disable self-collision within the rig
RIG_GROUP_INDEX = -7

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------
def to_screen(world_v):
    return int(world_v[0] * PPM), int(SCREEN_H - world_v[1] * PPM)

def poly_verts_for(body, hx, hy):
    local = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    c = body.transform
    return [to_screen(c * v) for v in local]

def clamp(v, lo, hi): return max(lo, min(hi, v))

# ------------------------------------------------------------
# Contact Listener for damage
# ------------------------------------------------------------
class ImpulseDamageListener(b2ContactListener):
    def __init__(self):
        super().__init__()
        self.impulses = []  # (bodyA, bodyB, impulse_mag)

    def PostSolve(self, contact, impulse):
        normal_impulse = sum(impulse.normalImpulses)
        if normal_impulse <= 0:
            return
        a = contact.fixtureA.body
        b = contact.fixtureB.body
        self.impulses.append((a, b, normal_impulse))

# ------------------------------------------------------------
# Bone & Muscle
# ------------------------------------------------------------
class Bone:
    def __init__(self, world, pos, size, angle=0.0, density=1.0, friction=0.4, category="bone"):
        self.world = world
        self.size = size  # (hx, hy)
        body = world.CreateDynamicBody(position=pos, angle=angle, linearDamping=2.0, angularDamping=2.4)
        fixture = body.CreateFixture(
            shape=b2PolygonShape(box=size),
            density=density,
            friction=friction,
            restitution=0.02
        )
        f = fixture.filterData
        f.groupIndex = RIG_GROUP_INDEX
        fixture.filterData = f

        body.userData = {"category": category, "hp": 100.0 if category == "enemy" else None}
        self.body = body
        self.fixture = fixture

    def render(self, surf, color):
        hx, hy = self.size
        pygame.draw.polygon(surf, color, poly_verts_for(self.body, hx, hy), 0)

class Muscle:
    def __init__(self, world, body_a, anchor_a, body_b, anchor_b,
                 rest_length, min_length_factor=0.55, max_length_factor=1.45,
                 base_hz=4.0, base_damp=0.55, strength=1.0, name="muscle"):
        self.world = world
        self.body_a = body_a
        self.body_b = body_b
        self.local_a = anchor_a
        self.local_b = anchor_b
        self.base_hz = base_hz
        self.base_damp = base_damp
        self.strength = strength
        self.name = name

        self.rest_length = rest_length
        self.min_length = rest_length * min_length_factor
        self.max_length = rest_length * max_length_factor
        self.activation = 0.0
        self.training = False

        jd = b2DistanceJointDef()
        jd.bodyA = body_a
        jd.bodyB = body_b
        jd.localAnchorA = anchor_a
        jd.localAnchorB = anchor_b
        jd.length = self.rest_length
        jd.frequencyHz = self.base_hz
        jd.dampingRatio = self.base_damp
        jd.collideConnected = False
        self.joint = self.world.CreateJoint(jd)

        # Sync rest length to actual initial distance
        wa = self.body_a.GetWorldPoint(self.local_a)
        wb = self.body_b.GetWorldPoint(self.local_b)
        actual = (b2Vec2(wb) - b2Vec2(wa)).length
        if actual > 1e-4:
            self.rest_length = actual
            self.min_length = self.rest_length * min_length_factor
            self.max_length = self.rest_length * max_length_factor
            self.joint.length = float(self.rest_length)

    def set_activation(self, a): self.activation = clamp(a, 0.0, 1.0)
    def set_training(self, enable: bool): self.training = enable

    def current_world_anchors(self):
        wa = self.body_a.GetWorldPoint(self.local_a)
        wb = self.body_b.GetWorldPoint(self.local_b)
        return wa, wb

    def update(self, dt):
        contraction = 0.85 * self.activation
        target_len = clamp(self.rest_length * (1.0 - contraction), self.min_length, self.max_length)
        self.joint.length = float(target_len)
        self.joint.frequencyHz = self.base_hz + 6.0 * self.activation * (
                    0.6 + 0.4 * clamp(self.strength, 0.0, 3.0))  # was +10.0 *
        self.joint.dampingRatio = clamp(self.base_damp + 0.25 * self.activation, 0.15, 1.0)

        wa, wb = self.current_world_anchors()
        d = b2Vec2(wb) - b2Vec2(wa)
        dist = d.length
        if dist > 1e-4:
            dirv = d / dist
            mavg = 0.5 * (self.body_a.mass + self.body_b.mass)
            force_mag = 220.0 * self.activation * self.strength * mavg  # was 520.0 *
            f = force_mag * dirv * -1.0
            self.body_a.ApplyForce(f, wa, True)
            self.body_b.ApplyForce(-f, wb, True)

        if self.training and self.activation > 0.5:
            self.strength = min(self.strength + 0.03 * dt, 31.0)

    def render(self, surf):
        wa, wb = self.current_world_anchors()
        col = COL_MUSCLE_ACTIVE if self.activation > 0.25 else COL_MUSCLE_IDLE
        pygame.draw.line(surf, col, to_screen(wa), to_screen(wb), 3)

# ------------------------------------------------------------
# Rig Setup
# ------------------------------------------------------------
class TopDownFighter:
    def __init__(self, world, origin):
        self.world = world
        self.origin = origin
        self.walk_speed = 50
        self.turn_speed = 50
        self.rotation = 0

        # Torso (bigger)
        self.torso = Bone(world, pos=origin, size=(0.35, 0.35), density=2.0, category="torso")
        # allow rotation, but damp it
        self.torso.body.fixedRotation = False
        self.torso.body.linearDamping = 5.0
        self.torso.body.angularDamping = 10.0

        # friction joint to static anchor (top-down feel; allows turning but damps drift)
        self._ground_anchor = self.world.CreateStaticBody()
        fj = b2FrictionJointDef()
        fj.Initialize(self._ground_anchor, self.torso.body, self.torso.body.worldCenter)
        fj.maxForce = self.torso.body.mass * 28.0
        fj.maxTorque = self.torso.body.mass * 6.0  # lets A/D turn; damps idle yaw
        self.torso_friction = self.world.CreateJoint(fj)

        SCALE = 1.25
        upper_len, upper_w = .43 * SCALE, 0.12 * SCALE
        lower_len, lower_w = .43 * SCALE, 0.12 * SCALE
        hand_len, hand_w = 0.18 * SCALE, 0.18 * SCALE

        # Shoulder anchored at the right edge of the torso (+ small gap)
        torso_hx = 0.40  # half-width you used for the torso box

        # ---- Right arm ----
        shoulder_pos_r = (self.origin[0] + torso_hx + 0.05, self.origin[1])

        # World anchors for the joints (east in local build pose)
        elbow_pos_r = (shoulder_pos_r[0] + upper_len, shoulder_pos_r[1])
        wrist_pos_r = (elbow_pos_r[0] + lower_len, elbow_pos_r[1])
        right_hand_tip = (wrist_pos_r[0] + hand_len, wrist_pos_r[1])

        # Bodies are centered at the midpoint between their joint anchors
        upper_center_r = ((shoulder_pos_r[0] + elbow_pos_r[0]) * 0.5, shoulder_pos_r[1])
        lower_center_r = ((elbow_pos_r[0] + wrist_pos_r[0]) * 0.5, elbow_pos_r[1])
        hand_center_r = ((wrist_pos_r[0] + right_hand_tip[0]) * 0.5, wrist_pos_r[1])

        # Create bodies aligned along +X (angle=0), sized to span the distance
        self.upper_r = Bone(self.world, pos=upper_center_r, size=(upper_len * 0.5, upper_w * 0.5), density=1.0,
                            category="bone")
        self.lower_r = Bone(self.world, pos=lower_center_r, size=(lower_len * 0.5, lower_w * 0.5), density=1.0,
                            category="bone")
        self.hand_r = Bone(self.world, pos=hand_center_r, size=(hand_len * 0.5, hand_w * 0.5), density=0.6,
                           category="hand")
        self.hand_r.body.userData["category"] = "hand"
        self.hand_r.body.bullet = True

        # Shoulder R
        jd = b2RevoluteJointDef()
        jd.Initialize(self.torso.body, self.upper_r.body, b2Vec2(*shoulder_pos_r))
        jd.enableLimit = True
        jd.lowerAngle = math.radians(-95)  # allow swing back
        jd.upperAngle = math.radians(170)  # and far forward (for north punch)
        jd.enableMotor = True
        jd.maxMotorTorque = 900.0
        self.shoulder_r = self.world.CreateJoint(jd)

        # Elbow R
        jd = b2RevoluteJointDef()
        jd.Initialize(self.upper_r.body, self.lower_r.body, b2Vec2(*elbow_pos_r))
        jd.enableLimit = True
        jd.lowerAngle = math.radians(5)
        jd.upperAngle = math.radians(145)
        jd.enableMotor = True
        jd.maxMotorTorque = 700.0
        self.elbow_r = self.world.CreateJoint(jd)

        # Wrist R
        jd = b2RevoluteJointDef()
        jd.Initialize(self.lower_r.body, self.hand_r.body, b2Vec2(*wrist_pos_r))
        jd.enableLimit = True
        jd.lowerAngle = math.radians(-10)  # rigid-ish fist
        jd.upperAngle = math.radians(+10)
        jd.enableMotor = True
        jd.maxMotorTorque = 420.0
        self.wrist_r = self.world.CreateJoint(jd)

        # Right arm muscles
        # Right pec (torso -> upper_r), mirror X anchors
        self.muscle_pec_r = Muscle(
            self.world,
            self.torso.body, anchor_a=b2Vec2(+0.25, +0.10),
            body_b=self.upper_r.body, anchor_b=b2Vec2(-upper_len * 0.45, +0.10),
            rest_length=0.32, min_length_factor=0.55, max_length_factor=1.35,
            base_hz=4.0, base_damp=0.55, strength=1.20, name="pec_r"
        )

        # Right bicep (upper_r -> lower_r)
        self.muscle_bicep_r = Muscle(
            self.world,
            self.upper_r.body, anchor_a=b2Vec2(+upper_len * 0.20, +0.10),
            body_b=self.lower_r.body, anchor_b=b2Vec2(-lower_len * 0.15, +0.10),
            rest_length=0.38, min_length_factor=0.55, max_length_factor=1.45,
            base_hz=4.0, base_damp=0.55, strength=1.15, name="bicep_r"
        )

        # Right triceps (upper_r -> lower_r)
        self.muscle_triceps_r = Muscle(
            self.world,
            self.upper_r.body, anchor_a=b2Vec2(+upper_len * 0.20, -0.10),
            body_b=self.lower_r.body, anchor_b=b2Vec2(-lower_len * 0.15, -0.10),
            rest_length=0.40, min_length_factor=0.60, max_length_factor=1.45,
            base_hz=4.0, base_damp=0.55, strength=1.15, name="triceps_r"
        )

        # ---- Left arm ----
        shoulder_pos_l = (self.origin[0] - torso_hx - 0.05, self.origin[1])
        elbow_pos_l = (shoulder_pos_l[0] - upper_len, shoulder_pos_l[1])
        wrist_pos_l = (elbow_pos_l[0] - lower_len, elbow_pos_l[1])
        hand_tip_l = (wrist_pos_l[0] - hand_len, wrist_pos_l[1])

        upper_center_l = ((shoulder_pos_l[0] + elbow_pos_l[0]) * 0.5, shoulder_pos_l[1])
        lower_center_l = ((elbow_pos_l[0] + wrist_pos_l[0]) * 0.5, elbow_pos_l[1])
        hand_center_l = ((wrist_pos_l[0] + hand_tip_l[0]) * 0.5, wrist_pos_l[1])

        self.upper_l = Bone(self.world, pos=upper_center_l,
                            size=(upper_len * 0.5, upper_w * 0.5),
                            angle=math.pi, density=1.0, category="bone")

        self.lower_l = Bone(self.world, pos=lower_center_l,
                            size=(lower_len * 0.5, lower_w * 0.5),
                            angle=math.pi, density=1.0, category="bone")

        self.hand_l = Bone(self.world, pos=hand_center_l,
                           size=(hand_len * 0.5, hand_w * 0.5),
                           angle=math.pi, density=0.6, category="hand")

        self.hand_l.body.userData["category"] = "hand"
        self.hand_l.body.bullet = True

        # Shoulder L
        jd = b2RevoluteJointDef()
        jd.Initialize(self.torso.body, self.upper_l.body, b2Vec2(*shoulder_pos_l))
        jd.enableLimit = True
        jd.lowerAngle = math.radians(-170)  # was -95
        jd.upperAngle = math.radians(95)  # was 170
        jd.enableMotor = True
        jd.maxMotorTorque = 900.0
        self.shoulder_l = self.world.CreateJoint(jd)

        # Elbow L
        jd = b2RevoluteJointDef()
        jd.Initialize(self.upper_l.body, self.lower_l.body, b2Vec2(*elbow_pos_l))
        jd.enableLimit = True
        # CHANGED: mirror the elbow bend range to negative
        jd.lowerAngle = math.radians(-145)
        jd.upperAngle = math.radians(-5)
        jd.enableMotor = True
        jd.maxMotorTorque = 700.0
        self.elbow_l = self.world.CreateJoint(jd)

        # Wrist L
        jd = b2RevoluteJointDef()
        jd.Initialize(self.lower_l.body, self.hand_l.body, b2Vec2(*wrist_pos_l))
        jd.enableLimit = True
        jd.lowerAngle = math.radians(-10)
        jd.upperAngle = math.radians(+10)
        jd.enableMotor = True
        jd.maxMotorTorque = 420.0
        self.wrist_l = self.world.CreateJoint(jd)

        # Left arm muscles
        # Left pec (torso -> upper_l)
        self.muscle_pec_l = Muscle(
            self.world,
            self.torso.body, anchor_a=b2Vec2(-0.25, +0.10),
            body_b=self.upper_l.body, anchor_b=b2Vec2(-upper_len * 0.45, -0.10),
            rest_length=0.32, min_length_factor=0.55, max_length_factor=1.35,
            base_hz=4.0, base_damp=0.55, strength=1.20, name="pec_l"
        )

        # Left bicep (upper_l -> lower_l)
        self.muscle_bicep_l = Muscle(
            self.world,
            self.upper_l.body, anchor_a=b2Vec2(upper_len * 0.20, 0.10),
            body_b=self.lower_l.body, anchor_b=b2Vec2(-lower_len * 0.15, 0.10),
            rest_length=0.38, min_length_factor=0.55, max_length_factor=1.45,
            base_hz=4.0, base_damp=0.55, strength=1.15, name="bicep_l"
        )
        # Left triceps (upper_l -> lower_l)
        self.muscle_triceps_l = Muscle(
            self.world,
            self.upper_l.body, anchor_a=b2Vec2(upper_len * 0.20, -0.10),
            body_b=self.lower_l.body, anchor_b=b2Vec2(-lower_len * 0.15, -0.10),
            rest_length=0.40, min_length_factor=0.60, max_length_factor=1.45,
            base_hz=4.0, base_damp=0.55, strength=1.15, name="triceps_l"
        )

        # Add all the muscles to the rig
        self.muscles = [
            self.muscle_pec_r, self.muscle_bicep_r, self.muscle_triceps_r,
            self.muscle_pec_l, self.muscle_bicep_l, self.muscle_triceps_l
        ]

    @staticmethod
    def _wrap_pi(x): return (x + math.pi) % (2 * math.pi) - math.pi

    def _drive_joint_to(self, joint, target_angle_rad, gain=8.0, max_speed=16.0, torque_limit=500.0):
        err = self._wrap_pi(target_angle_rad - joint.angle)
        joint.motorSpeed = clamp(gain * err, -max_speed, +max_speed)
        joint.maxMotorTorque = torque_limit
        joint.enableMotor = True

    def _drive_wrist_abs(self, desired_abs, gain=10.0, max_speed=18.0, torque_limit=420.0):
        # wrist joint angle is (hand.angle - lower.angle)
        target_rel = desired_abs - self.lower_r.body.angle
        self._drive_joint_to(self.wrist_r, target_rel, gain, max_speed, torque_limit)

    def reset_pose(self):
        for b in [self.torso, self.upper_r, self.lower_r, self.hand_r]:
            body = b.body
            x, y = self.origin
            jitter = (random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02))
            body.position = (x + jitter[0], y + jitter[1])
            body.angle = 0.0
            body.linearVelocity = (0.0, 0.0)
            body.angularVelocity = 0.0

        for m in self.muscles:
            m.set_activation(0.0)
            m.joint.length = m.rest_length

    def update(self, dt, keys, training=False):
        # training flags for all muscles
        for m in self.muscles:
            m.set_training(training)

        # movement (top-down drift + yaw with A/D)
        move = b2Vec2(0, 0)
        if keys[pygame.K_w]: move += (0.0, 60.0)
        if keys[pygame.K_s]: move += (0.0, -60.0)
        if keys[pygame.K_q]: move += (-60.0, 0.0)
        if keys[pygame.K_e]: move += (60.0, 0.0)
        if move.lengthSquared > 0:
            self.torso.body.ApplyForceToCenter(move, True)
        if keys[pygame.K_a]: self.torso.body.ApplyTorque(+60.0, True)
        if keys[pygame.K_d]: self.torso.body.ApplyTorque(-60.0, True)

        # inputs
        space = keys[pygame.K_SPACE]
        hold = keys[pygame.K_h]
        edge_space = space and not getattr(self, "_space_prev", False)

        # default state
        if not hasattr(self, "phase"):
            self.phase, self.timer = "idle", 0.0

        # forward world angle (north relative to torso orientation)
        forward_abs = self.torso.body.angle + math.radians(90)

        # ---------------- phase machine (drives BOTH arms) ----------------
        if self.phase == "idle":
            if edge_space:
                self.phase, self.timer = "wind", 0.05
            elif hold:
                # guard / flex
                self.muscle_pec_r.set_activation(0.30);
                self.muscle_pec_l.set_activation(0.30)
                self.muscle_triceps_r.set_activation(0.08);
                self.muscle_triceps_l.set_activation(0.08)
                self.muscle_bicep_r.set_activation(1.00);
                self.muscle_bicep_l.set_activation(1.00)

                # shoulder: right +60°, left -60°
                self._drive_joint_to(self.shoulder_r, math.radians(60), gain=9.0, max_speed=14.0, torque_limit=700.0)
                self._drive_joint_to(self.shoulder_l, math.radians(-60), gain=9.0, max_speed=14.0, torque_limit=700.0)

                # elbows: mirror sign (right +110°, left -110°)
                self._drive_joint_to(self.elbow_r, math.radians(110), gain=9.0, max_speed=16.0, torque_limit=750.0)
                self._drive_joint_to(self.elbow_l, math.radians(-110), gain=9.0, max_speed=16.0, torque_limit=750.0)

                # wrists small flex
                self._drive_joint_to(self.wrist_r, math.radians(5), gain=7.0, max_speed=12.0, torque_limit=300.0)
                self._drive_joint_to(self.wrist_l, math.radians(5), gain=7.0, max_speed=12.0, torque_limit=300.0)

            else:
                # idle pose
                self.muscle_pec_r.set_activation(0.15);
                self.muscle_pec_l.set_activation(0.15)
                self.muscle_triceps_r.set_activation(0.12);
                self.muscle_triceps_l.set_activation(0.12)
                self.muscle_bicep_r.set_activation(0.12);
                self.muscle_bicep_l.set_activation(0.12)

                # shoulder: right +18°, left -18°
                self._drive_joint_to(self.shoulder_r, math.radians(18), gain=7.5, max_speed=12.0, torque_limit=420.0)
                self._drive_joint_to(self.shoulder_l, math.radians(-18), gain=7.5, max_speed=12.0, torque_limit=420.0)

                # elbows: right +60°, left -60°
                self._drive_joint_to(self.elbow_r, math.radians(60), gain=7.5, max_speed=12.0, torque_limit=420.0)
                self._drive_joint_to(self.elbow_l, math.radians(-60), gain=7.5, max_speed=12.0, torque_limit=420.0)

                # wrists relaxed
                self._drive_joint_to(self.wrist_r, 0.0, gain=6.0, max_speed=10.0, torque_limit=300.0)
                self._drive_joint_to(self.wrist_l, 0.0, gain=6.0, max_speed=10.0, torque_limit=300.0)

        elif self.phase == "wind":
            # preload (slight retract) — smoother acceleration
            self.muscle_pec_r.set_activation(0.25);
            self.muscle_pec_l.set_activation(0.25)
            self.muscle_triceps_r.set_activation(0.10);
            self.muscle_triceps_l.set_activation(0.10)
            self.muscle_bicep_r.set_activation(0.85);
            self.muscle_bicep_l.set_activation(0.85)

            # shoulder: right +70°, left -70°
            self._drive_joint_to(self.shoulder_r, math.radians(70), gain=10.0, max_speed=16.0, torque_limit=700.0)
            self._drive_joint_to(self.shoulder_l, math.radians(-70), gain=10.0, max_speed=16.0, torque_limit=700.0)

            # elbows: right +95°, left -95°
            self._drive_joint_to(self.elbow_r, math.radians(95), gain=10.0, max_speed=16.0, torque_limit=700.0)
            self._drive_joint_to(self.elbow_l, math.radians(-95), gain=10.0, max_speed=16.0, torque_limit=700.0)

            # wrists neutral
            self._drive_joint_to(self.wrist_r, 0.0, gain=8.0, max_speed=12.0, torque_limit=300.0)
            self._drive_joint_to(self.wrist_l, 0.0, gain=8.0, max_speed=12.0, torque_limit=300.0)

            self.timer -= dt
            if self.timer <= 0.0:
                self.phase, self.timer = "strike", 0.14

        elif self.phase == "strike":
            # extend straight forward (north)
            self.muscle_pec_r.set_activation(1.00);
            self.muscle_pec_l.set_activation(1.00)
            self.muscle_triceps_r.set_activation(1.00);
            self.muscle_triceps_l.set_activation(1.00)
            self.muscle_bicep_r.set_activation(0.05);
            self.muscle_bicep_l.set_activation(0.05)

            # shoulder: right +90°, left -90°
            self._drive_joint_to(self.shoulder_r, math.radians(90), gain=12.0, max_speed=22.0, torque_limit=950.0)
            self._drive_joint_to(self.shoulder_l, math.radians(-90), gain=12.0, max_speed=22.0, torque_limit=950.0)

            # elbows: right +8°, left -8°
            self._drive_joint_to(self.elbow_r, math.radians(8), gain=12.0, max_speed=22.0, torque_limit=850.0)
            self._drive_joint_to(self.elbow_l, math.radians(-8), gain=12.0, max_speed=22.0, torque_limit=850.0)

            # rigid fists: align both hands with forward world angle
            self._drive_wrist_abs(forward_abs, gain=9.5, max_speed=18.0, torque_limit=420.0)
            target_rel_L = forward_abs - self.lower_l.body.angle
            self._drive_joint_to(self.wrist_l, target_rel_L, gain=9.5, max_speed=18.0, torque_limit=420.0)

            self.timer -= dt
            if self.timer <= 0.0:
                self.phase, self.timer = "follow", 0.12

        elif self.phase == "follow":
            # slight overshoot
            self.muscle_pec_r.set_activation(0.85);
            self.muscle_pec_l.set_activation(0.85)
            self.muscle_triceps_r.set_activation(0.90);
            self.muscle_triceps_l.set_activation(0.90)
            self.muscle_bicep_r.set_activation(0.09);
            self.muscle_bicep_l.set_activation(0.09)

            # shoulder: right +100°, left -100°
            self._drive_joint_to(self.shoulder_r, math.radians(100), gain=10.0, max_speed=18.0, torque_limit=850.0)
            self._drive_joint_to(self.shoulder_l, math.radians(-100), gain=10.0, max_speed=18.0, torque_limit=850.0)

            # elbows: right +10°, left -10°
            self._drive_joint_to(self.elbow_r, math.radians(10), gain=10.0, max_speed=18.0, torque_limit=750.0)
            self._drive_joint_to(self.elbow_l, math.radians(-10), gain=10.0, max_speed=18.0, torque_limit=750.0)

            # keep fists facing forward during follow-through
            self._drive_wrist_abs(forward_abs, gain=8.5, max_speed=16.0, torque_limit=420.0)
            target_rel_L = forward_abs - self.lower_l.body.angle
            self._drive_joint_to(self.wrist_l, target_rel_L, gain=8.5, max_speed=16.0, torque_limit=420.0)

            self.timer -= dt
            if self.timer <= 0.0:
                self.phase, self.timer = "recover", 0.10

        elif self.phase == "recover":
            # back to ready
            self.muscle_pec_r.set_activation(0.25);
            self.muscle_pec_l.set_activation(0.25)
            self.muscle_triceps_r.set_activation(0.20);
            self.muscle_triceps_l.set_activation(0.20)
            self.muscle_bicep_r.set_activation(0.25);
            self.muscle_bicep_l.set_activation(0.25)

            # shoulder: right +65°, left -65°
            self._drive_joint_to(self.shoulder_r, math.radians(65), gain=8.0, max_speed=16.0, torque_limit=650.0)
            self._drive_joint_to(self.shoulder_l, math.radians(-65), gain=8.0, max_speed=16.0, torque_limit=650.0)

            # elbows: right +60°, left -60°
            self._drive_joint_to(self.elbow_r, math.radians(60), gain=8.0, max_speed=16.0, torque_limit=650.0)
            self._drive_joint_to(self.elbow_l, math.radians(-60), gain=8.0, max_speed=16.0, torque_limit=650.0)

            # wrists relaxed
            self._drive_joint_to(self.wrist_r, 0.0, gain=7.0, max_speed=12.0, torque_limit=300.0)
            self._drive_joint_to(self.wrist_l, 0.0, gain=7.0, max_speed=12.0, torque_limit=300.0)

            self.timer -= dt
            if self.timer <= 0.0:
                self.phase = "idle"

        self._space_prev = space

        # update muscle springs last (after targets set)
        for m in self.muscles:
            m.update(dt)

    def render(self, surf):
        self.torso.render(surf, COL_TORSO)
        self.upper_r.render(surf, COL_BONE)
        self.lower_r.render(surf, COL_BONE)
        self.hand_r.render(surf, COL_HAND)
        self.upper_l.render(surf, COL_BONE)
        self.lower_l.render(surf, COL_BONE)
        self.hand_l.render(surf, COL_HAND)
        for m in self.muscles: m.render(surf)

    @property
    def hand_body(self):
        return self.hand_r.body

# ------------------------------------------------------------
# Enemy target
# ------------------------------------------------------------
class EnemyDummy:
    def __init__(self, world, pos, radius=0.25):
        self.world = world
        bd = world.CreateDynamicBody(position=pos, linearDamping=10.0, angularDamping=12.0)

        fd = b2FixtureDef(
            shape=b2CircleShape(pos=(0, 0), radius=radius),
            density=3.0,  # heavier, harder to push
            friction=1.0,  # more tangential grip
            restitution=0.0  # no bounce
        )
        bd.CreateFixture(fd)
        bd.userData = {"category": "enemy", "hp": 100.0}
        self.body = bd
        self.radius = radius

        # anchor friction to world to resist sliding/rotation from hits
        self._anchor = world.CreateStaticBody()
        fj = b2FrictionJointDef()
        fj.Initialize(self._anchor, self.body, self.body.worldCenter)
        fj.maxForce = self.body.mass * 18.0  # tune down/up knockback
        fj.maxTorque = 40.0  # limit spin from glancing blows
        self.friction_joint = world.CreateJoint(fj)

    def render(self, surf):
        pos = to_screen(self.body.position)
        pygame.draw.circle(surf, COL_ENEMY, pos, int(self.radius * PPM))

# ------------------------------------------------------------
# World setup
# ------------------------------------------------------------
def make_world():
    world = b2World(gravity=(0, 0), doSleep=True)
    ground = world.CreateStaticBody(position=(SCREEN_W / (2 * PPM), 0.4))
    ground.CreateEdgeChain([(-8, 0), (8, 0)])
    left = world.CreateStaticBody();  left.CreateEdgeChain([(0.5, 0), (0.5, 10)])
    right = world.CreateStaticBody(); right.CreateEdgeChain([(SCREEN_W / PPM - 0.5, 0), (SCREEN_W / PPM - 0.5, 10)])
    top = world.CreateStaticBody();   top.CreateEdgeChain([(0, SCREEN_H / PPM - 0.5), (SCREEN_W / PPM, SCREEN_H / PPM - 0.5)])
    return world

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Top-Down Muscle Rig Prototype (pybox2d + pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    world = make_world()
    listener = ImpulseDamageListener()
    world.contactListener = listener

    fighter = TopDownFighter(world, origin=(6.0, 4.0))
    enemy = EnemyDummy(world, pos=(6.0, 6.0), radius=0.35)  # in front (north) of torso

    running = True
    training = False
    total_time = 0.0

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                if e.key == pygame.K_r: fighter.reset_pose()
                if e.key == pygame.K_t:
                    training = not training
                    print(f"Training: {training}")

        keys = pygame.key.get_pressed()
        fighter.update(DT, keys, training=training)

        world.Step(DT, VEL_ITERS, POS_ITERS)
        total_time += DT

        # Damage resolution
        for (a, b, imp) in listener.impulses:
            bodies = [a, b]
            cats = [x.userData.get("category") if x.userData else None for x in bodies]
            if "enemy" in cats:
                idx_enemy = cats.index("enemy")
                idx_other = 1 - idx_enemy
                other_cat = cats[idx_other]
                if other_cat in ("hand", "bone", "torso"):
                    muscle_bonus = 1.0
                    if other_cat == "hand":
                        act = 0.5 * (fighter.muscle_triceps_r.activation + fighter.muscle_pec_r.activation)
                        muscle_bonus = 1.0 + 1.5 * act * (0.5 + 0.5 * fighter.muscle_triceps_r.strength)
                    dmg = 0.08 * imp * muscle_bonus
                    enemy.body.userData["hp"] = max(0.0, enemy.body.userData["hp"] - dmg)
        listener.impulses.clear()

        # Render
        screen.fill(BG)
        pygame.draw.line(screen, (80, 80, 90), (0, SCREEN_H - int(0.4 * PPM)), (SCREEN_W, SCREEN_H - int(0.4 * PPM)), 2)
        fighter.render(screen)
        enemy.render(screen)

#        HUD
        y = 8
        for m in fighter.muscles:
            txt = f"{m.name}: act={m.activation:.2f} len={m.joint.length:.2f} str={m.strength:.2f}"
            surf = font.render(txt, True, (230, 230, 230))
            screen.blit(surf, (8, y)); y += 18

        ehp = enemy.body.userData["hp"]
        hp_txt = font.render(f"Enemy HP: {ehp:6.1f}", True, (255, 120, 120))
        screen.blit(hp_txt, (SCREEN_W - 200, 10))

        hint = [
            "SPACE: punch forward (north)  |  H: flex/guard  |  T: training",
            "W/S forward/back, Q/E strafe, A/D spin torso  |  R: reset"
        ]
        for i, line in enumerate(hint):
            s = font.render(line, True, (180, 180, 180))
            screen.blit(s, (8, SCREEN_H - 20 * (len(hint) - i)))

        pygame.display.flip()
        clock.tick(int(1.0 / DT))

    pygame.quit()

if __name__ == "__main__":
    main()
