"""PULSE category abilities with linked parameters."""

PULSE_ABILITIES = (
    ('pressurize', 'raise pressure inside the object', 'повысить давление внутри объекта'),
    ('depressurize', 'lower pressure inside the object', 'понизить давление внутри объекта'),
    ('vent', 'release pressure from the object', 'стравить давление из объекта'),
    ('purge', 'flush the object of contents', 'продуть объект от содержимого'),
    ('fill', 'put contents into the object', 'заполнить объект содержимым'),
    ('refill', "top the object's contents back up", 'дозаполнить содержимое объекта'),
    ('drain', 'remove contents from the object', 'удалить содержимое из объекта'),
    ('empty', 'remove all contents from the object', 'удалить всё содержимое объекта'),
)

PULSE_PARAMETERS = {
    'fluid': (
        ('empty', 'surface_tension', 'add', 3.21798, 'alter the target physical parameter'),
    ),
}
