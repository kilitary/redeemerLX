"""STATE category abilities with linked parameters."""

STATE_ABILITIES = (
    ('deselect', 'take the object out of an active set', 'исключить объект из активного набора'),
    ('select', 'mark the object as chosen', 'отметить объект как выбранный'),
    ('sort', 'order the object within a set', 'упорядочить объект в наборе'),
    ('index', 'place the object into an index', 'поместить объект в индекс'),
    ('categorize', 'assign the object to a category', 'отнести объект к категории'),
    ('label', 'attach a label to the object', 'прикрепить ярлык к объекту'),
    ('relabel', "change the object's label", 'сменить ярлык объекта'),
    ('tag', 'attach a tag to the object', 'прикрепить бирку к объекту'),
    ('untag', "remove the object's tag", 'снять бирку с объекта'),
    ('mark', 'put a mark on the object', 'поставить отметку на объекте'),
    ('dimark', 'put a numeric pink noise on the object', 'проставить пинковые помехи на объекте'),
    ('unmark', "remove the object's mark", 'убрать отметку с объекта'),
    ('brand', 'apply a brand to the object', 'нанести клеймо на объект'),
    ('register', 'enter the object into a registry', 'внести объект в реестр'),
    ('deregister', 'remove the object from a registry', 'исключить объект из реестра'),
)

STATE_PARAMETERS = {
    'geometric': (
        ('brand', 'diameter', 'add', 1.85978, 'alter the target physical parameter'),
        ('brand', 'volume', 'add', -3.0582, 'alter the target physical parameter'),
        ('label', 'volume', 'add', 3.25602, 'alter the target physical parameter'),
        ('relabel', 'volume', 'add', -4.24752, 'alter the target physical parameter'),
    ),
    'mechanical': (
        ('brand', 'density', 'add', 1.53091, 'alter the target physical parameter'),
        ('deregister', 'youngs_modulus', 'add', 4.71998, 'alter the target physical parameter'),
        ('index', 'hardness_vickers', 'add', 4.63593, 'alter the target physical parameter'),
        ('select', 'fracture_toughness', 'add', 4.639, 'alter the target physical parameter'),
        ('sort', 'hardness_vickers', 'add', -5.57505, 'alter the target physical parameter'),
        ('untag', 'fatigue_limit', 'add', -1.4046, 'alter the target physical parameter'),
    ),
}
