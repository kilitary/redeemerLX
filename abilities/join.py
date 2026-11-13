"""JOIN category abilities with linked parameters."""

JOIN_ABILITIES = (
    ('connect', 'join the object to another object', 'соединить объект с другим объектом'),
    ('merge', 'combine the object with another object', 'объединить объект с другим объектом'),
    ('weld', 'fuse the object with heat', 'сварить объект с помощью нагрева'),
    ('solder', 'join the object using molten solder', 'соединить объект расплавленным припоем'),
    ('rivet', 'fasten the object with a rivet', 'скрепить объект заклёпкой'),
    ('glue', 'adhere the object with adhesive', 'приклеить объект клеем'),
    ('clip', 'attach the object with a clip', 'прикрепить объект зажимом'),
    ('pin', 'secure the object with a pin', 'закрепить объект штифтом'),
    ('fasten', 'attach the object firmly', 'прочно прикрепить объект'),
    ('mount', 'place the object onto a fixture', 'установить объект на крепёж'),
    ('amalgamate', 'blend the object with another', 'смешать объект с другим'),
)

JOIN_PARAMETERS = {
    'electrical': (
        ('merge', 'dielectric_strength', 'add', 5.8188, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('amalgamate', 'density', 'add', -5.47189, 'alter the target physical parameter'),
        ('amalgamate', 'tensile_strength', 'add', -5.80432, 'alter the target physical parameter'),
        ('connect', 'density', 'add', 3.81778, 'alter the target physical parameter'),
        ('connect', 'yield_strength', 'add', -5.79749, 'alter the target physical parameter'),
        ('fasten', 'density', 'add', -3.53056, 'alter the target physical parameter'),
        ('glue', 'hardness_rockwell', 'add', 4.31439, 'alter the target physical parameter'),
        ('mount', 'poisson_ratio', 'add', -3.8474, 'alter the target physical parameter'),
        ('pin', 'fatigue_limit', 'add', 2.95076, 'alter the target physical parameter'),
        ('rivet', 'fatigue_limit', 'add', 2.36221, 'alter the target physical parameter'),
        ('solder', 'shear_strength', 'add', -5.15729, 'alter the target physical parameter'),
        ('weld', 'yield_strength', 'add', 2.22535, 'alter the target physical parameter'),
    ),
    'thermal': (
        ('clip', 'melting_point', 'add', -2.06215, 'alter the target physical parameter'),
        ('glue', 'specific_heat', 'add', 4.59267, 'alter the target physical parameter'),
        ('mount', 'melting_point', 'add', 4.3256, 'alter the target physical parameter'),
    ),
}
