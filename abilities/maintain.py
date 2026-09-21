"""MAINTAIN category abilities with linked parameters."""

MAINTAIN_ABILITIES = (
    ('calibrate', 'adjust the object to a standard', 'откалибровать объект по эталону'),
    ('recalibrate', 'adjust the object back to a standard', 'перекалибровать объект по эталону'),
    ('tune', 'adjust the object for resonance', 'настроить объект на резонанс'),
    ('detune', 'move the object off resonance', 'сбить объект с резонанса'),
    ('repair', 'restore the object to working order', 'восстановить работоспособность объекта'),
    ('service', 'perform maintenance on the object', 'провести обслуживание объекта'),
    ('maintain', 'keep the object in working order', 'поддерживать объект в рабочем порядке'),
    ('lubricate', 'apply lubricant to the object', 'нанести смазку на объект'),
    ('oil', 'apply oil to the object', 'нанести масло на объект'),
    ('grease', 'apply grease to the object', 'нанести консистентную смазку на объект'),
    ('clean', 'remove dirt from the object', 'удалить грязь с объекта'),
    ('wash', 'clean the object with liquid', 'очистить объект жидкостью'),
    ('decontaminate', 'remove contaminants from the object', 'удалить загрязнения с объекта'),
    ('sterilize', 'make the object free of organisms', 'освободить объект от микроорганизмов'),
)

MAINTAIN_PARAMETERS = {
    'chemical': (
        ('grease', 'solubility', 'add', 4.16493, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('detune', 'density', 'add', -4.86418, 'alter the target physical parameter'),
        ('repair', 'shear_strength', 'add', 4.42698, 'alter the target physical parameter'),
    ),
    'thermal': (
        ('calibrate', 'thermal_conductivity', 'add', 5.26621, 'alter the target physical parameter'),
        ('grease', 'boiling_point', 'add', -4.6008, 'alter the target physical parameter'),
        ('lubricate', 'melting_point', 'add', 3.87581, 'alter the target physical parameter'),
        ('oil', 'melting_point', 'add', 3.15325, 'alter the target physical parameter'),
        ('recalibrate', 'thermal_expansion', 'add', 1.74292, 'alter the target physical parameter'),
        ('sterilize', 'boiling_point', 'add', 3.80019, 'alter the target physical parameter'),
        ('sterilize', 'melting_point', 'add', 5.04921, 'alter the target physical parameter'),
    ),
}
