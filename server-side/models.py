from dataclasses import dataclass
import abc

class ModelBase(abc.ABC):
    """Abstract base class."""
    
    def serialize(self):
        """Serialize an object to JSON, so it can be passed-around in HTTP queries.

        Returns:
            dict: JSON-serializable dictionary
        """
        return self.__dict__

@dataclass
class User(ModelBase):
    id_: int
    email: str
    fname: str
    sname: str

@dataclass
class Area(ModelBase):
    """Example :class:`Area` usage:
    
        .. code-block:: python
            :linenos:

            area = models.Area(
                owner = None, 
                name = "Besides the lake", 
                notes = "Besides the lake, avoiding the trees, left of the pond", 
                area_coords = [
                    (52.619274360887445, 24.0, 1.2393361009732562),
                    (52.619274360423945, 24.0, 1.2393361009734234),
                    (52.619272593850345, 24.0, 1.2346346239823423)
                ], 
                nogo_zones = [
                    [
                        (52.619534542345435, 24.0, 1.2393352345423454),
                        (52.619272345234545, 24.0, 1.2393234523452345),
                        (52.623454234523454, 24.0, 1.2334523452345234)
                    ],
                    [
                        (52.619534542345435, 24.0, 1.2393352345423454),
                        (52.619272345234545, 24.0, 1.2393234523452345),
                        (52.623454234523454, 24.0, 1.2334523452345234)
                    ]
                ]
            )
    """
    owner: User
    name: str
    notes: str
    area_coords: list
    nogo_zones: list

    def to_keypairs(self):
        """Alternative serialization method, so that 'true' JSON is returned,
        that is, key-value pairs only. It is annoying that we have to do this,
        for example we cannot have bare lists. Serializing loses the ``owner`` attribute.

        This method is currently un-used. If we do need to use it, we should also
        make a deserialization method too.
        
        For example, the example area becomes:

        .. code-block:: json
            :linenos:

            {
                "name": "Besides the lake",
                "notes": "Besides the lake, avoiding the trees, left of the pond",
                "area_coords": {
                    "0": {
                        "x": 52.619274360887445,
                        "y": 24.0,
                        "z": 1.2393361009732562
                    },
                    "1": {
                        "x": 52.619274360423944,
                        "y": 24.0,
                        "z": 1.2393361009734234
                    },
                    "2": {
                        "x": 52.61927259385035,
                        "y": 24.0,
                        "z": 1.2346346239823422
                    }
                },
                "nogo_zones": {
                    "0": {
                        "0": {
                            "x": 52.619534542345434,
                            "y": 24.0,
                            "z": 1.2393352345423454
                        },
                        "1": {
                            "x": 52.61927234523454,
                            "y": 24.0,
                            "z": 1.2393234523452346
                        },
                        "2": {
                            "x": 52.62345423452346,
                            "y": 24.0,
                            "z": 1.2334523452345234
                        }
                    },
                    "1": {
                        "0": {
                            "x": 52.619534542345434,
                            "y": 24.0,
                            "z": 1.2393352345423454
                        },
                        "1": {
                            "x": 52.61927234523454,
                            "y": 24.0,
                            "z": 1.2393234523452346
                        },
                        "2": {
                            "x": 52.62345423452346,
                            "y": 24.0,
                            "z": 1.2334523452345234
                        }
                    }
                }
            }

        
        """
        area_coords = self.area_coords
        nogo_zones = self.nogo_zones

        out = self.__dict__
        out["area_coords"] = {}
        del out["owner"]
             
        for i, coords in enumerate(area_coords, 0):
            out["area_coords"][i] = coord_tuple_to_xyz(coords)

        out["nogo_zones"] = {}
        for i, nogo_zone in enumerate(nogo_zones, 0):
            out["nogo_zones"][i] = {}
            for j, coords in enumerate(nogo_zone, 0):
                out["nogo_zones"][i][j] = coord_tuple_to_xyz(coords)

        return out

    # override
    def serialize(self):
        """Serializing a :class:`Area` object makes it lose its :class:`User` attribute."""
        out = self.__dict__
        del out["owner"]
        return out

def deserialize(json_: dict, type_: type, **kwargs):
    """
    Deserialize a given JSON dictionary into type ``type_``.
    If any information was lost in serialization, add it back in ``**kwargs``;
    for example a :class:`Area` must have its :class:`User` added back- e.g.:

    .. code-block:: python
        :linenos:

        ser = area.serialize()
        area_again = models.deserialize(ser, models.Area, owner = None)

    Args:
        json_ (dict): A :class:`ModelBase` object serialised to JSON
        type_ (type[ModelBase]): The object to serialize to

    Returns:
        ``type_``: The type set in the argument

    """
    json_.update(kwargs)
    return type_(**json_)

def coord_tuple_to_xyz(coord):
    return {chr(i): j for i, j in enumerate(coord, 120)}
