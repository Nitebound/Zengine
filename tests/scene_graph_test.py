from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Vec2D:
    x: float
    y: float

@dataclass
class Transform:
    x: float
    y: float
    rotation: float
    scale_x: float
    scale_y: float

@dataclass
class Parent:
    parent_entity: int

@dataclass
class Children:
    children: List[int] = field(default_factory=list)

@dataclass
class SpriteRenderer:
    image: any
    offset_x: float = 0
    offset_y: float = 0

@dataclass
class RectangleRenderer:
    width: int
    height: int
    color: tuple
    offset_x: float = 0
    offset_y: float = 0

class EntityManager:
    def __init__(self):
        self._next_entity_id = 0
        self.components = {}

    def create_entity(self):
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def add_component(self, entity, component):
        comp_type = type(component)
        if comp_type not in self.components:
            self.components[comp_type] = {}
        self.components[comp_type][entity] = component

    def get_component(self, entity, comp_type):
        return self.components.get(comp_type, {}).get(entity)

    def get_entities_with(self, *comp_types):
        if not comp_types:
            return set()
        sets = [set(self.components.get(ct, {}).keys()) for ct in comp_types]
        return set.intersection(*sets)


def render_system(renderer, entity_manager):
    for eid in entity_manager.get_entities_with(Transform, RectangleRenderer):
        transform = entity_manager.get_component(eid, Transform)
        rect = entity_manager.get_component(eid, RectangleRenderer)
        renderer.draw_rect(rect.color, transform.x + rect.offset_x, transform.y + rect.offset_y, rect.width, rect.height)

    for eid in entity_manager.get_entities_with(Transform, SpriteRenderer):
        transform = entity_manager.get_component(eid, Transform)
        sprite = entity_manager.get_component(eid, SpriteRenderer)
        renderer.draw_sprite(sprite.image, transform.x + sprite.offset_x, transform.y + sprite.offset_y)

def update_scene_graph(entity_manager):
    # Traverse parent -> children and update children's world transform
    for parent_eid in entity_manager.get_entities_with(Children, Transform):
        parent_transform = entity_manager.get_component(parent_eid, Transform)
        children = entity_manager.get_component(parent_eid, Children).children

        for child_eid in children:
            child_transform = entity_manager.get_component(child_eid, Transform)
            child_transform.x += parent_transform.x
            child_transform.y += parent_transform.y
