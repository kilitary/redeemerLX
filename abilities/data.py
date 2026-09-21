"""DATA category abilities with linked parameters."""

DATA_ABILITIES = (
    ('reset', 'return the object to its initial state', 'вернуть объект в исходное состояние'),
    ('encode', 'convert the object into another form', 'преобразовать объект в другую форму'),
    ('decode', 'recover the original form of the object', 'восстановить исходную форму объекта'),
    ('encrypt', "scramble the object's content", 'зашифровать содержимое объекта'),
    ('decrypt', "restore the object's plain content", 'восстановить открытое содержимое объекта'),
    ('format', "lay out the object's storage", 'разметить хранилище объекта'),
    ('reformat', "re-lay the object's storage", 'переразметить хранилище объекта'),
    ('initialize', 'set up the object for first use', 'подготовить объект к первому использованию'),
    ('configure', "set the object's operating parameters", 'задать рабочие параметры объекта'),
    ('deconfigure', "clear the object's operating parameters", 'сбросить рабочие параметры объекта'),
    ('upgrade', 'raise the object to a newer version', 'повысить объект до новой версии'),
    ('downgrade', 'return the object to an older version', 'вернуть объект к старой версии'),
    ('update', 'bring the object to the latest state', 'привести объект к актуальному состоянию'),
    ('patch', 'apply a fix to the object', 'применить исправление к объекту'),
    ('dispatch', 'send the object to its destination', 'отправить объект к месту назначения'),
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
