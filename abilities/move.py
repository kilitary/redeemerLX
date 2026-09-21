"""MOVE category abilities with linked parameters."""

MOVE_ABILITIES = (
    ('align', 'arrange the object along a shared axis', 'выровнять объект по общей оси'),
    ('misalign', 'offset the object from its intended axis', 'сместить объект с заданной оси'),
    ('rotate', 'spin the object around an axis', 'вращать объект вокруг оси'),
    ('rotate-back', 'spin the object back to its original orientation', 'вернуть объект в исходную ориентацию'),
    ('translate', 'alters the object position', 'изменить позицию объекта в локальной геометрии'),
    ('mirror', 'flip the object as if reflected', 'отразить объект как в зеркале'),
)

MOVE_PARAMETERS = {
    'mechanical': (
        ('align', 'mass', 'add', 4.76377, 'alter the target physical parameter'),
        ('rotate', 'hardness_brinell', 'add', 3.94905, 'alter the target physical parameter'),
        ('rotate', 'yield_strength', 'add', 3.66538, 'alter the target physical parameter'),
        ('rotate-back', 'yield_strength', 'add', 4.28508, 'alter the target physical parameter'),
        ('translate', 'compressive_strength', 'add', -3.61424, 'alter the target physical parameter'),
    ),
}
