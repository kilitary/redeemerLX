"""DATA category abilities with linked parameters."""

DATA_ABILITIES = (
    ('reset', 'return the object to its initial state', 'вернуть объект в исходное состояние'),
    ('encode', 'convert the object into another form', 'преобразовать объект в другую форму'),
    ('format', "lay out the object's storage", 'разметить хранилище объекта'),
    ('downgrade', 'return the object to an older version', 'вернуть объект к старой версии'),
    ('patch', 'apply a fix to the object', 'применить исправление к объекту'),
)

DATA_PARAMETERS = {
    'acoustic': (
        ('encode', 'acoustic_impedance', 'add', 3.38574, 'alter the target physical parameter'),
        ('format', 'acoustic_impedance', 'add', 4.60176, 'alter the target physical parameter'),
        ('reset', 'damping_coefficient', 'add', 1.72496, 'alter the target physical parameter'),
    ),
    'electrical': (
        ('downgrade', 'relative_permittivity', 'add', 2.3643, 'alter the target physical parameter'),
        ('patch', 'electrical_resistivity', 'add', 2.20856, 'alter the target physical parameter'),
    ),
}
