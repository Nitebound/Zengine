# zengine/ecs/systems/animation_system.py

import numpy as np
from zengine.ecs.systems.system import System
from zengine.ecs.components.animation import Animation  # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}

class AnimationSystem(System):
    """
    Drives per‐node Animation components.  You’ll need to
    populate Animation.samplers/channels from your glTF data
    so this can sample and write into each node’s Transform.
    """
    def __init__(self):
        super().__init__()
        # track playback time per‐animation entity
        self._times: dict[int, float] = {}

    def on_update(self, dt: float):
        for eid in self.em.get_entities_with(Animation):
            anim = self.em.get_component(eid, Animation)
            t = self._times.get(eid, 0.0) + dt
            self._times[eid] = t

            # TODO: for each sampler/channel in anim,
            # sample value = sampler.sample(t) and write into
            # the target node’s Transform component.
            # This stub does nothing until you wire in glTF keyframes.
