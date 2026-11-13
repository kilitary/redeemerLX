"""THERMAL category abilities with linked parameters."""

THERMAL_ABILITIES = (
    ('firm-up', "harden the object's firmware", 'закрепить прошивку объекта'),
    ('freeze', 'lower the object below freezing', 'охладить объект ниже точки замерзания'),
    ('temper', 'harden the object by reheating', 'закалить объект повторным нагревом'),
)

THERMAL_PARAMETERS = {
    'thermal': (
        ('firm-up', 'boiling_point', 'add', 5.75779, 'alter the target physical parameter'),
        ('freeze', 'autoignition_temp', 'add', 5.34143, 'alter the target physical parameter'),
        ('temper', 'specific_heat', 'add', 4.07781, 'alter the target physical parameter'),
    ),
}
