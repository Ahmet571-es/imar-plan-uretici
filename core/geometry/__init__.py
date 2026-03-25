"""
Geometri alt modülü — kat planı üretiminde kullanılan
oda slotları, koridor düzenleri, yerleştirme ve finalizasyon.
"""

from core.geometry.room_slots import RoomSlot, _create_room_slots, _default_room_program
from core.geometry.corridor_layouts import (
    LAYOUT_TYPES,
    _select_layout_type,
    _create_corridor_spine,
    _create_center_corridor,
    _create_l_corridor,
    _create_t_corridor,
    _create_short_corridor,
    _create_open_plan_corridor,
)
from core.geometry.room_placement import (
    _get_sun_zone,
    _place_rooms_in_zone,
    _place_single_room,
    _find_best_zone,
    _force_place_remaining,
)
from core.geometry.plan_finalization import _convert_to_plan_rooms

__all__ = [
    "RoomSlot",
    "_create_room_slots",
    "_default_room_program",
    "LAYOUT_TYPES",
    "_select_layout_type",
    "_create_corridor_spine",
    "_create_center_corridor",
    "_create_l_corridor",
    "_create_t_corridor",
    "_create_short_corridor",
    "_create_open_plan_corridor",
    "_get_sun_zone",
    "_place_rooms_in_zone",
    "_place_single_room",
    "_find_best_zone",
    "_force_place_remaining",
    "_convert_to_plan_rooms",
]
