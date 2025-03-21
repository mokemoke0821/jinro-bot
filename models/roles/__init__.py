from .base_role import BaseRole
from .villager import Villager
from .werewolf import Werewolf
from .seer import Seer
from .madman import Madman
from .hunter import Hunter
from .medium import Medium
from .fox import Fox

# 役職名とクラスのマッピング
ROLE_MAP = {
    "村人": Villager,
    "人狼": Werewolf,
    "占い師": Seer,
    "狂人": Madman,
    "狩人": Hunter,
    "霊媒師": Medium,
    "妖狐": Fox
}

__all__ = [
    'BaseRole',
    'Villager',
    'Werewolf',
    'Seer',
    'Madman',
    'Hunter',
    'Medium',
    'Fox',
    'ROLE_MAP'
]
