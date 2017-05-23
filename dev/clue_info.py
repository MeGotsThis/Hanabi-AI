from typing import List, Optional

from enums import Color, Value


class ClueState:
    def __init__(self,
                 turn: int,
                 isCritical: bool,
                 hand: List[int],
                 indexes: List[int],
                 was_clued: List[bool],
                 discard_index: Optional[int],
                 worthless: bool, *,
                 color: Optional[Color]=None,
                 value: Optional[Value]=None,
                 play_colors: List[Color]=None,
                 later_colors: List[Color]=None,
                 discard_color: List[Color]=None,
                 discard_values: List[Value]=None) -> None:
        self.turn: int = turn
        self.critical: bool = isCritical
        self.color: Optional[Color] = color
        self.value: Optional[Value] = value
        self.hand: List[int] = hand
        self.indexes: List[int] = indexes
        self.wasClued: List[bool] = was_clued
        self.discardIndex: Optional[int] = discard_index
        self.worthlessDiscard: bool = worthless
        self.playColors: List[Color] = play_colors
        self.laterColors: List[Color] = later_colors
        self.discardColors: List[Color] = discard_color
        self.discardValues: List[Value] = discard_values
