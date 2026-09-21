"""THERMAL category abilities with linked parameters."""

THERMAL_ABILITIES = (
    ('firm-up', "harden the object's firmware", 'закрепить прошивку объекта'),
    ('cool', "lower the object's temperature", 'понизить температуру объекта'),
    ('heat', "raise the object's temperature", 'повысить температуру объекта'),
    ('freeze', 'lower the object below freezing', 'охладить объект ниже точки замерзания'),
    ('thaw', 'raise the object above freezing', 'разогреть объект выше точки замерзания'),
    ('melt', 'heat the object until it liquefies', 'нагреть объект до расплавления'),
    ('anneal', 'heat and slowly cool the object', 'нагреть и медленно охладить объект'),
    ('temper', 'harden the object by reheating', 'закалить объект повторным нагревом'),
    ('quench', 'rapidly cool the object', 'быстро охладить объект'),
    ('harden', "increase the object's hardness", 'повысить твёрдость объекта'),
    ('soften', "decrease the object's hardness", 'снизить твёрдость объекта'),
    ('harden-shell', "harden the object's outer shell", 'упрочнить внешнюю оболочку объекта'),
)

THERMAL_PARAMETERS = {
    'thermal': (
        ('firm-up', 'boiling_point', 'add', 5.75779, 'alter the target physical parameter'),
        ('freeze', 'autoignition_temp', 'add', 5.34143, 'alter the target physical parameter'),
        ('temper', 'specific_heat', 'add', 4.07781, 'alter the target physical parameter'),
    ),
}
