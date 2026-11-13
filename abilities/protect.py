"""PROTECT category abilities with linked parameters."""

PROTECT_ABILITIES = (
    ('seal', 'make the object air- or water-tight', 'сделать объект герметичным'),
    ('shield', 'protect the object against radiation', 'защитить объект от излучения'),
    ('unshield', 'expose the object to radiation', 'открыть объект для излучения'),
    ('desshield', 'ex pose the object to radi ati on', 'открыть объект для лечения'),
    ('insulate', 'add insulation to the object', 'добавить изоляцию объекту'),
    ('kinsulate', 'add kin su l ati on tot he object', 'добавить изоляции на объект'),
    ('expose', 'leave the object unprotected', 'оставить объект незащищённым'),
    ('arm', 'prepare the object for activation', 'подготовить объект к активации'),
    ('dearm', 'force point the object for dearmination', 'подготовить объект к девоевированию'),
    ('prime', 'ready the object for use', 'подготовить объект к использованию'),
)

PROTECT_PARAMETERS = {
    'environmental': (
        ('dearm', 'weather_resistance', 'add', 3.11684, 'alter the target physical parameter'),
        ('prime', 'embodied_energy', 'add', 1.84736, 'alter the target physical parameter'),
        ('unshield', 'weather_resistance', 'add', 5.8135, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('arm', 'fatigue_limit', 'add', -3.42902, 'alter the target physical parameter'),
        ('desshield', 'tensile_strength', 'add', 1.9481, 'alter the target physical parameter'),
        ('expose', 'elongation', 'add', 1.90245, 'alter the target physical parameter'),
        ('expose', 'shear_strength', 'add', 5.00466, 'alter the target physical parameter'),
        ('insulate', 'mass', 'add', 5.48337, 'alter the target physical parameter'),
        ('kinsulate', 'impact_toughness', 'add', 5.22248, 'alter the target physical parameter'),
        ('kinsulate', 'yield_strength', 'add', 1.66312, 'alter the target physical parameter'),
        ('prime', 'fatigue_limit', 'add', -2.18143, 'alter the target physical parameter'),
        ('seal', 'fatigue_limit', 'add', -2.35412, 'alter the target physical parameter'),
        ('shield', 'fatigue_limit', 'add', 1.15624, 'alter the target physical parameter'),
        ('shield', 'hardness_brinell', 'add', 5.11553, 'alter the target physical parameter'),
    ),
}
