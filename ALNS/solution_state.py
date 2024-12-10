import copy


class CevrpState:
    def __init__(self, routes, unassigned=None):
        self.routes = routes
        self.unassigned = unassigned if unassigned is not None else []


def duplicate(self):
    """Creates a duplicate of the current state."""
    # Makes a deep copy of 'routes' and a shallow copy of 'unassigned'
    routes_copy = copy.deepcopy(self.routes)
    unassigned_copy = self.unassigned.copy()
    return CevrpState(routes_copy, unassigned_copy)