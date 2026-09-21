"""OPERATE category abilities with linked parameters."""

OPERATE_ABILITIES = (
    ('touch', 'make physical contact with the object', 'вступить в физический контакт с объектом'),
    ('scale', 'change the size of the object', 'изменить размер объекта'),
    ('invert', 'turn the object inside out or upside down', 'вывернуть объект наизнанку или вверх дном'),
    ('tighten', 'increase tension on the object', 'увеличить натяжение объекта'),
    ('loosen', 'decrease tension on the object', 'уменьшить натяжение объекта'),
    ('lock', 'secure the object against movement', 'зафиксировать объект от движения'),
    ('unlock', 'release the object from its lock', 'освободить объект от замка'),
    ('integrate', 'combine the object into a whole', 'включить объект в целое'),
)

OPERATE_PARAMETERS = {
    'manufacturing': (
        ('loosen', 'warranty_period', 'add', 4.6839, 'alter the target physical parameter'),
    ),
}
