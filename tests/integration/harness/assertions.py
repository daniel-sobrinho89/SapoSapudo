from math import hypot


def assert_moved(before, entity, minimum=8):
    distance = hypot(entity.x - before[0], entity.y - before[1])
    assert distance >= minimum, f"entidade moveu apenas {distance:.1f}px"


def assert_in_attack_range(a, b, range_=32):
    distance = hypot(a.x - b.x, a.y - b.y)
    assert distance <= range_ + 4, f"distância final {distance:.1f}px > {range_ + 4}px"


def assert_target_damaged(before, target):
    assert target.vida < before, f"alvo não recebeu dano: vida {target.vida}"


class IntegrationFailure(AssertionError):
    def __init__(self, message, trace=None):
        super().__init__(message)
        self.trace = trace
