from .base_role import BaseRole
from .villager import Villager
from .werewolf import Werewolf
from .seer import Seer
from .madman import Madman
from .hunter import Hunter
from .medium import Medium
from .fox import Fox
from .mason import Mason
from .heretic import Heretic
from .cat import Cat
from .prophet import Prophet
from .fanatic import Fanatic

# 役職名とクラスのマッピング
ROLE_MAP = {
    "村人": Villager,
    "人狼": Werewolf,
    "占い師": Seer,
    "狂人": Madman,
    "狩人": Hunter,
    "霊媒師": Medium,
    "妖狐": Fox,
    "共有者": Mason,
    "背徳者": Heretic,
    "猫又": Cat,
    "預言者": Prophet,
    "狂信者": Fanatic
}

def create_role_instance(role_name, player):
    """
    役職名からクラスのインスタンスを生成する
    
    Args:
        role_name (str): 役職名
        player (Player): プレイヤーインスタンス
        
    Returns:
        BaseRole: 役職クラスのインスタンス（継承クラス）
        None: 存在しない役職名の場合
    """
    role_class = ROLE_MAP.get(role_name)
    if role_class:
        return role_class(player)
    return None

__all__ = [
    'BaseRole',
    'Villager',
    'Werewolf',
    'Seer',
    'Madman',
    'Hunter',
    'Medium',
    'Fox',
    'Mason',
    'Heretic',
    'Cat',
    'Prophet',
    'Fanatic',
    'ROLE_MAP',
    'create_role_instance'
]
