from dataclasses import dataclass

@dataclass
class User:
    id_: int
    email: str
    fname: str
    sname: str

@dataclass
class Area:
    owner: User
    name: str
    notes: str
    area_coords: list[tuple[float]]
    nogo_zones: list[list[tuple[float]]]