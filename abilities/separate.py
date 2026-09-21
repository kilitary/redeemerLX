"""SEPARATE category abilities with linked parameters."""

SEPARATE_ABILITIES = (
    ('split', 'divide the object into smaller parts', 'разделить объект на более мелкие части'),
    ('extract', 'pull the object out of its socket or cavity', 'извлечь объект из гнезда или полости'),
    ('isolate', 'separate the object from its surroundings', 'отделить объект от окружения'),
    ('disintegrate', 'break the object into fragments', 'разбить объект на фрагменты'),
    ('segregate', 'keep the object apart from others', 'держать объект отдельно от других'),
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
