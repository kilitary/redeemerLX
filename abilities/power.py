"""POWER category abilities with linked parameters."""

POWER_ABILITIES = (
    ('power-on', 'apply power to the object', 'подать питание на объект'),
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
