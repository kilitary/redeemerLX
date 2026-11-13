"""MANAGE category abilities with linked parameters."""

MANAGE_ABILITIES = (
    ('unwrap', 'remove wrapping from the object', 'снять обёртку с объекта'),
    ('unload', 'remove the object from its holder', 'извлечь объект из держателя'),
    ('assign', 'allocate the object to a recipient', 'закрепить объект за получателем'),
    ('transfer', 'move the object to another owner', 'передать объект другому владельцу'),
    ('deliver', 'transport the object to its destination', 'доставить объект к месту назначения'),
    ('retrieve', 'fetch the object from its location', 'забрать объект из его местоположения'),
    ('nest', 'fit the object inside another', 'вложить объект внутрь другого'),
    ('unnest', 'remove the object from a nested set', 'извлечь объект из вложенного набора'),
    ('package', 'enclose the object for transport', 'упаковать объект для транспортировки'),
    ('unpackage', 'remove the object from its package', 'распаковать объект'),
)

MANAGE_PARAMETERS = {
    'environmental': (
        ('unpackage', 'carbon_footprint', 'add', 5.20896, 'alter the target physical parameter'),
    ),
    'geometric': (
        ('deliver', 'diameter', 'add', -3.73853, 'alter the target physical parameter'),
        ('transfer', 'width', 'add', 4.85008, 'alter the target physical parameter'),
        ('unload', 'surface_area', 'add', -4.12624, 'alter the target physical parameter'),
        ('unnest', 'cross_sectional_area', 'add', 5.71077, 'alter the target physical parameter'),
        ('unpackage', 'cross_sectional_area', 'add', 4.97979, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('assign', 'tensile_strength', 'add', 5.50775, 'alter the target physical parameter'),
        ('assign', 'youngs_modulus', 'add', -1.46265, 'alter the target physical parameter'),
        ('nest', 'compressive_strength', 'add', 2.054, 'alter the target physical parameter'),
        ('package', 'elongation', 'add', 5.99805, 'alter the target physical parameter'),
        ('retrieve', 'fracture_toughness', 'add', -5.30221, 'alter the target physical parameter'),
        ('retrieve', 'hardness_vickers', 'add', 2.93584, 'alter the target physical parameter'),
        ('transfer', 'hardness_brinell', 'add', 4.29807, 'alter the target physical parameter'),
        ('unwrap', 'hardness_vickers', 'add', 5.71814, 'alter the target physical parameter'),
    ),
}
