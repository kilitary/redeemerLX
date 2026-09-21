"""SHAPE category abilities with linked parameters."""

SHAPE_ABILITIES = (
    ('skew', 'tilt the object off a straight line', 'наклонить объект относительно прямой линии'),
    ('distort', 'deform the object away from its normal shape', 'деформировать объект, отклонив от обычной формы'),
    ('straighten', 'remove bends and kinks from the object', 'устранить изгибы и перегибы объекта'),
    ('bend', 'curve the object into an angle', 'согнуть объект под углом'),
    ('fold', 'bend the object onto itself', 'сложить объект пополам'),
    ('unfold', 'lay the folded object back out', 'развернуть сложенный объект обратно'),
    ('stretch', 'pull the object into a longer shape', 'растянуть объект в более длинную форму'),
    ('compress', 'press the object into a smaller volume', 'сжать объект в меньший объём'),
    ('expand', 'grow the object into a larger volume', 'расширить объект до большего объёма'),
    ('flatten', 'press the object into a thin, flat form', 'расплющить объект в тонкую плоскую форму'),
    ('extrude', 'push the object through a shaping die', 'протянуть объект через формующий профиль'),
    ('mold', 'shape the object in a cavity', 'придать объекту форму в полости'),
    ('cast', 'form the object by pouring into a mould', 'отлить объект, залив в форму'),
    ('forge', 'shape the object by hammering', 'выковать объект ударами'),
    ('compress-data', "reduce the object's data footprint", 'уменьшить объём данных объекта'),
    ('decompress', "restore the object's full data footprint", 'восстановить полный объём данных объекта'),
    ('magnify', "increase the object's apparent size", 'увеличить видимый размер объекта'),
    ('minify', "decrease the object's apparent size", 'уменьшить видимый размер объекта'),
    ('fold-in', 'tuck the object into a compact form', 'сложить объект в компактную форму'),
    ('expand-out', 'unfurl the object to full form', 'развернуть объект в полную форму'),
)

SHAPE_PARAMETERS = {
    'geometric': (
        ('compress-data', 'width', 'add', 3.71387, 'alter the target physical parameter'),
        ('expand-out', 'height', 'add', 4.33149, 'alter the target physical parameter'),
        ('fold-in', 'height', 'add', 2.13633, 'alter the target physical parameter'),
        ('magnify', 'volume', 'add', -5.3129, 'alter the target physical parameter'),
        ('mold', 'surface_area', 'add', 1.19413, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('bend', 'compressive_strength', 'add', 1.02838, 'alter the target physical parameter'),
        ('bend', 'hardness_vickers', 'add', 1.86279, 'alter the target physical parameter'),
        ('compress-data', 'fracture_toughness', 'add', -5.0407, 'alter the target physical parameter'),
        ('distort', 'mass', 'add', 3.56398, 'alter the target physical parameter'),
        ('expand', 'yield_strength', 'add', 5.91527, 'alter the target physical parameter'),
        ('expand-out', 'fracture_toughness', 'add', 4.64093, 'alter the target physical parameter'),
        ('extrude', 'shear_strength', 'add', 2.69152, 'alter the target physical parameter'),
        ('flatten', 'fracture_toughness', 'add', 2.05928, 'alter the target physical parameter'),
        ('fold', 'hardness_vickers', 'add', 3.68726, 'alter the target physical parameter'),
        ('fold-in', 'yield_strength', 'add', -4.7322, 'alter the target physical parameter'),
        ('forge', 'youngs_modulus', 'add', 5.10547, 'alter the target physical parameter'),
        ('skew', 'poisson_ratio', 'add', 2.30845, 'alter the target physical parameter'),
    ),
}
