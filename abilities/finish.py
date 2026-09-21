"""FINISH category abilities with linked parameters."""

FINISH_ABILITIES = (
    ('polish', 'smooth and shine the object surface', 'отполировать и отшлифовать поверхность объекта'),
    ('buff', 'rub the object to a shine', 'натереть объект до блеска'),
    ('sand', 'abrade the object surface', 'отшлифовать поверхность объекта'),
    ('grind', 'wear the object down with an abrasive', 'стачивать объект абразивом'),
    ('sharpen', 'give the object a sharp edge', 'заточить объект до острой кромки'),
    ('blunt', "remove the object's sharp edge", 'снять острую кромку объекта'),
)

FINISH_PARAMETERS = {
    'mechanical': (
        ('blunt', 'mass', 'add', 4.30346, 'alter the target physical parameter'),
        ('grind', 'density', 'add', 2.45292, 'alter the target physical parameter'),
        ('sharpen', 'density', 'add', 2.79706, 'alter the target physical parameter'),
        ('sharpen', 'youngs_modulus', 'add', -2.08162, 'alter the target physical parameter'),
    ),
}
