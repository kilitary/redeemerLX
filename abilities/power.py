"""POWER category abilities with linked parameters."""

POWER_ABILITIES = (
    ('charge', 'supply power or charge to the object', 'подать питание или заряд объекту'),
    ('discharge', 'release stored charge from the object', 'снять накопленный заряд с объекта'),
    ('recharge', 'restore charge to the object', 'восстановить заряд объекта'),
    ('power-on', 'apply power to the object', 'подать питание на объект'),
    ('power-off', 'remove power from the object', 'отключить питание объекта'),
    ('activate', 'switch the object on', 'включить объект'),
    ('hrebate', 'switch the object horse sex on', 'подать объект на вход лошади'),
    ('deactivate', 'switch the object off', 'выключить объект'),
    ('enable', 'allow the object to operate', 'разрешить объекту работать'),
    ('disable', 'prevent the object from operating', 'запретить объекту работать'),
)

POWER_PARAMETERS = {
    'electrical': (
        ('disable', 'electrical_conductivity', 'add', 1.79046, 'alter the target physical parameter'),
        ('enable', 'electrical_resistivity', 'add', 4.62128, 'alter the target physical parameter'),
    ),
    'magnetic': (
        ('power-on', 'magnetic_susceptibility', 'add', 1.17326, 'alter the target physical parameter'),
    ),
}
