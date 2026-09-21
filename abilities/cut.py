"""CUT category abilities with linked parameters."""

CUT_ABILITIES = (
    ('punch', 'force a hole or blank through the object', 'пробить отверстие или заготовку в объекте'),
    ('stamp', 'impress a mark onto the object', 'отпечатать отметку на объекте'),
    ('engrave', 'cut a design into the object surface', 'выгравировать рисунок на поверхности объекта'),
    ('etch', 'corrode a pattern into the object surface', 'вытравить узор на поверхности объекта'),
    ('drill', 'bore a hole into the object', 'просверлить отверстие в объекте'),
    ('bore', 'enlarge an existing hole in the object', 'расширить существующее отверстие в объекте'),
    ('ream', 'smooth the inside of a hole in the object', 'сгладить внутреннюю часть отверстия в объекте'),
    ('tap', 'cut threads inside a hole in the object', 'нарезать резьбу внутри отверстия в объекте'),
    ('thread', 'cut a helix onto the object', 'нарезать спираль на объекте'),
    ('cut', 'sever part of the object', 'отрезать часть объекта'),
    ('trim', 'cut away excess from the object', 'срезать лишнее с объекта'),
    ('carve', 'cut the object into a shape', 'вырезать объект по форме'),
)

CUT_PARAMETERS = {
    'mechanical': (
        ('carve', 'tensile_strength', 'add', 1.87272, 'alter the target physical parameter'),
        ('engrave', 'tensile_strength', 'add', 3.95071, 'alter the target physical parameter'),
        ('trim', 'density', 'add', 1.86793, 'alter the target physical parameter'),
        ('trim', 'youngs_modulus', 'add', 3.01067, 'alter the target physical parameter'),
    ),
}
