"""SCAN category abilities with linked parameters."""

SCAN_ABILITIES = (
    ('inspect', 'examine the object for faults', 'осмотреть объект на предмет неисправностей'),
    ('test', 'exercise the object to check it works', 'проверить объект на работоспособность'),
    ('retest', 'exercise the object again', 'проверить объект повторно'),
    ('monitor', "watch the object's state", 'наблюдать за состоянием объекта'),
    ('measure', 'take measurements of the object', 'снять показания объекта'),
    ('weigh', "measure the object's mass", 'измерить массу объекта'),
    ('meter', "measure the object's consumption", 'измерить потребление объекта'),
    ('serialize', 'give the object a serial identity', 'присвоить объекту серийный номер'),
)

SCAN_PARAMETERS = {
    'geometric': (
        ('inspect', 'diameter', 'add', 5.14174, 'alter the target physical parameter'),
        ('inspect', 'volume', 'add', 4.49697, 'alter the target physical parameter'),
        ('test', 'volume', 'add', 1.35316, 'alter the target physical parameter'),
        ('weigh', 'surface_area', 'add', 1.29196, 'alter the target physical parameter'),
    ),
    'optical': (
        ('monitor', 'transparency', 'add', 2.271, 'alter the target physical parameter'),
        ('retest', 'transparency', 'add', 1.50965, 'alter the target physical parameter'),
    ),
}
