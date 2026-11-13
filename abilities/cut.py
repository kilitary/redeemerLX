"""CUT category abilities with linked parameters."""

CUT_ABILITIES = (
    ('engrave', 'cut a design into the object surface', 'выгравировать рисунок на поверхности объекта'),
    ('trim', 'cut away excess from the object', 'срезать лишнее с объекта'),
    ('carve', 'cut the object into a shape', 'вырезать объект по форме'),
)

CUT_PARAMETERS = {
    'mechanical': (
        ('carve', 'tensile_strength', 'add', 1.87272, 'alter the target physical parameter'),
        ('engrave', 'tensile_strength', 'add', 3.95071, 'alter the target physical parameter'),
        ('trim', 'density', 'add', 1.86793, 'alter the target physical parameter'),
        ('trim', 'youngs_modulus', 'add', 3.01067, 'alter the target physical parameter'),
    ),
}
