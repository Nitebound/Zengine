class EntityManager:
    def __init__(self):
        self._next_entity_id = 0
        self.components = {}

    def create_entity(self):
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def add_component(self, entity, component):
        ctype = type(component)
        if ctype not in self.components:
            self.components[ctype] = {}
        self.components[ctype][entity] = component

    def get_component(self, entity, ctype):
        return self.components.get(ctype, {}).get(entity)

    def get_entities_with(self, *ctypes):
        if not ctypes:
            return set()
        sets = [set(self.components.get(t, {}).keys()) for t in ctypes]
        return set.intersection(*sets)
