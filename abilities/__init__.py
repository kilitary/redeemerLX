# Ability categories with linked parameters

from abilities.scan import SCAN_ABILITIES, SCAN_PARAMETERS
from abilities.shape import SHAPE_ABILITIES, SHAPE_PARAMETERS
from abilities.pulse import PULSE_ABILITIES, PULSE_PARAMETERS
from abilities.move import MOVE_ABILITIES, MOVE_PARAMETERS
from abilities.cut import CUT_ABILITIES, CUT_PARAMETERS
from abilities.finish import FINISH_ABILITIES, FINISH_PARAMETERS
from abilities.join import JOIN_ABILITIES, JOIN_PARAMETERS
from abilities.separate import SEPARATE_ABILITIES, SEPARATE_PARAMETERS
from abilities.thermal import THERMAL_ABILITIES, THERMAL_PARAMETERS
from abilities.protect import PROTECT_ABILITIES, PROTECT_PARAMETERS
from abilities.power import POWER_ABILITIES, POWER_PARAMETERS
from abilities.data import DATA_ABILITIES, DATA_PARAMETERS
from abilities.maintain import MAINTAIN_ABILITIES, MAINTAIN_PARAMETERS
from abilities.manage import MANAGE_ABILITIES, MANAGE_PARAMETERS
from abilities.state import STATE_ABILITIES, STATE_PARAMETERS
from abilities.optics import OPTICS_ABILITIES, OPTICS_PARAMETERS
from abilities.operate import OPERATE_ABILITIES, OPERATE_PARAMETERS

ALL_ABILITIES = {
    'scan': SCAN_ABILITIES,
    'shape': SHAPE_ABILITIES,
    'pulse': PULSE_ABILITIES,
    'move': MOVE_ABILITIES,
    'cut': CUT_ABILITIES,
    'finish': FINISH_ABILITIES,
    'join': JOIN_ABILITIES,
    'separate': SEPARATE_ABILITIES,
    'thermal': THERMAL_ABILITIES,
    'protect': PROTECT_ABILITIES,
    'power': POWER_ABILITIES,
    'data': DATA_ABILITIES,
    'maintain': MAINTAIN_ABILITIES,
    'manage': MANAGE_ABILITIES,
    'state': STATE_ABILITIES,
    'optics': OPTICS_ABILITIES,
    'operate': OPERATE_ABILITIES,
}

ALL_PARAMETERS = {
    'scan': SCAN_PARAMETERS,
    'shape': SHAPE_PARAMETERS,
    'pulse': PULSE_PARAMETERS,
    'move': MOVE_PARAMETERS,
    'cut': CUT_PARAMETERS,
    'finish': FINISH_PARAMETERS,
    'join': JOIN_PARAMETERS,
    'separate': SEPARATE_PARAMETERS,
    'thermal': THERMAL_PARAMETERS,
    'protect': PROTECT_PARAMETERS,
    'power': POWER_PARAMETERS,
    'data': DATA_PARAMETERS,
    'maintain': MAINTAIN_PARAMETERS,
    'manage': MANAGE_PARAMETERS,
    'state': STATE_PARAMETERS,
    'optics': OPTICS_PARAMETERS,
    'operate': OPERATE_PARAMETERS,
}
