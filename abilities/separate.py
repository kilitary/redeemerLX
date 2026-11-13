"""SEPARATE category abilities with linked parameters."""

SEPARATE_ABILITIES = (
    ('isolate', 'separate the object from its surroundings', 'отделить объект от окружения'),
    ('disintegrate', 'break the object into fragments', 'разбить объект на фрагменты'),
)

SEPARATE_PARAMETERS = {
    'geometric': (
        ('disintegrate', 'height', 'add', -3.71903, 'alter the target physical parameter'),
        ('isolate', 'cross_sectional_area', 'add', 2.74204, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('isolate', 'poisson_ratio', 'add', 2.99435, 'alter the target physical parameter'),
    ),
}
