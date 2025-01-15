from ....config import *
from .... import logging_config
import logging 
from ...db import COUNTY_LOOKUP_DF, STATE_LOOKUP_DF
from ....funcs.utils import generate_permutations

from .LocationRecord import LocationRecord, LocationString

logger = logging.getLogger(__name__)
LOG_LEVEL = Config.logLevels.geog
logger.setLevel(Config.logLevels.geog)

class StateUS(BaseModel): 
    """
    Record-level model for ensuring consistent US state name attributes.
    """
    name: Optional[str] = None
    usps: Optional[str] = None
    fips: Optional[str] = None
 
    def __init__(self, 
                desig: Optional[str] = None, 
                /,
                name: Optional[str] = None,
                usps: Optional[str] = None,
                fips: Optional[str] = None): 
        
        ## Pre-init:
        # These annoying workarounds are to play nicely with pydantic.Basemodel.__init__() while adding a positional-only argument
        if desig is not None: 
            desig_dict = self._lookup_desig(desig)
        else: 
            desig_dict = None
            for desig in (name, usps, fips): 
                if desig: 
                    _desig_dict = self._lookup_desig(desig)
                    if desig_dict and desig_dict != _desig_dict: 
                        a,b = set(desig_dict.values()), set(_desig_dict.values())
                        diff = (a.difference(b)).union(b.difference(a))
                        raise ValueError(f"Inconsistent state designators: ({', '.join(diff)})")
                    else: 
                        desig_dict = _desig_dict
                    
        # Initialize super class 
        super().__init__(**desig_dict)

    def lookup(self, include_counties: bool = False): 
        df = STATE_LOOKUP_DF if not include_counties else COUNTY_LOOKUP_DF
        return df.filter(pl.col(f"state_name").eq(self.name) 
                               & pl.col(f"state_usps").eq(self.usps)
                               & pl.col(f"state_fips").eq(self.fips))

    @classmethod
    def _lookup_desig(cls, desig) -> dict:
        lookup = STATE_LOOKUP_DF.filter(pl.col(f"state_name").eq(desig) 
                               | pl.col(f"state_usps").eq(desig)
                               | pl.col(f"state_fips").eq(desig)).collect()
        if lookup.is_empty():
            raise ValueError(f'{desig} not valid state name, FIPS, or USPS')
        
        return {k.split("_")[1]:v for k,v in lookup.to_dicts()[0].items()}

    @classmethod
    def det_desig_type(cls, desig: str) -> Literal['name', 'usps', 'fips']: 
        """
        Determine if a value is a valid state fips, abbreviation, or name 
        """
        for k,v in cls._lookup_desig(desig).items():
            if v == desig: 
                return k
                        
    def to_record(self) -> LocationRecord: 

        return LocationRecord(state_name=self.name,
                        state_fips=self.fips,
                        state_usps=self.usps,
                        )
    
    def to_records(self) -> list[LocationRecord]: 
        """
        Includes for all counties information in the state.
        """
        rows = self.lookup(include_counties=True).collect().to_dicts()
        try: 
            output = []
            for row in rows:    
                location_str = str(LocationString(county_name=row['county_name'], state_usps=row['state_usps'])) 
                record = LocationRecord(state_name=row['state_name'],
                        state_fips=row['state_fips'],
                        state_usps=row['state_usps'],
                        county_fips=row['county_fips'],
                        county_name=row['county_name'],
                        location=location_str
                        )
                output.append(record)
            return output
        except KeyError as e:
                logger.error(row)
                raise e
        
    @classmethod
    def from_record(cls, r: LocationRecord) -> 'StateUS':
        return cls.__init__(name=r.state_name, usps=r.state_usps, fips=r.state_fips)
    
    @classmethod
    def random(cls, n: int = 1): 
        rows = STATE_LOOKUP_DF.select(['state_name', 'state_usps', 'state_fips'])\
            .collect()\
            .sample(n)\
            .rows()
        return [StateUS(name=r[0],
                       usps=r[1],
                       fips=r[2]) for r in rows]


    @model_validator(mode="before")
    @classmethod
    def _ensure_field_agreement(cls, data: dict) -> None:
        """
        Check that the combination of name, usps, and fips is valid for a US state.
        """

        all_attrs = ("name", "usps", "fips") # == cls.__annotations__.items()
        
        have_attrs = [(t[0], t[1:]) for t in generate_permutations(all_attrs)]

        for prim_attr_type, other_attr_types in have_attrs: 
            
            # Check the provided value for the primary attribute type is valid 
            given_prim_value = data[prim_attr_type]
            df_filtered = STATE_LOOKUP_DF.filter(pl.col(f"state_{prim_attr_type}").eq(given_prim_value)).collect()
            if df_filtered.shape[0] == 0: 
                raise ValueError(f"Invalid {prim_attr_type} in {data}") 
            
            # Check that the other attribute types agree with this value (or are None) 
            for other_attr in other_attr_types: 
                if not data.get(other_attr):
                    raise Warning(f'{other_attr} not provided.')
                else: 
                    expected_other_value = df_filtered.select(pl.col(f"state_{other_attr}")).rows()[0][-1]
                    if expected_other_value != data[other_attr]: 
                        raise ValueError(f"""Given {other_attr} ({data[other_attr]}) does not match expected ({expected_other_value})
                                     for {prim_attr_type} ({data[prim_attr_type]}]): {data}""")
        return data 
    
    @model_validator(mode="after")
    @classmethod
    def _ensure_at_least_one_provided(cls, data: Any ) -> None:
        """
        Check that at least one of 'name', 'usps', or 'fips' is provided
        """
        required_attrs = {"name", 'usps', 'fips'}
        for field in data: 
            if field[0] in required_attrs and field[1]:
                return data 
            
        raise ValueError(f"Provide at least one of {', '.join(required_attrs)}") 

    def __str__(self): 
        return (self.name)

    def __lt__(self, other): 
        return str(self) < str(other)