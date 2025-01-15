from ....config import *
from .... import logging_config
import logging 
from .StateUS import StateUS
from .FipsCode import CountyFips
from .LocationRecord import LocationRecord, LocationString

from ...db import COUNTY_LOOKUP_DF
from re import sub 


logger = logging.getLogger(__name__)
logger.setLevel(Config.logLevels.geog)

class CountyUS(BaseModel): 
    """
    Record-level model for ensuring US county matches lookup table (db.GEOG.countypop).

    NOTE: Do not run iteratively on the rows of a DataFrame (use db.GEOG.countypop).
    Repeated filters will slow down your code.
    """ 
    name: str
    state: StateUS
    fips: Optional[CountyFips] = None # not intended to initialize directly

    def __init__(self, 
            location_str: str = None , 
            /,
            name: str = None,
            state: Union[str, StateUS] = None,
            fips: CountyFips | None = None # not intended to initialize directly
            ):
        
        ## Construct from location_str 
        if location_str is not None: 
            _name, _state = CountyUS._parse_location_str(location_str)
        else: 
            _name, _state = name, state

        # Parse _state 
        match _state: 
            case str(): 
                _state = StateUS(_state)
            case StateUS():
                pass 
            case _:
                raise TypeError(f"Invalid type {type(_state)} for state ({_state})")
            
        # Look up County Fips
        _fips = CountyUS._lookup_county_fips(_name, _state)

        # Initialize super class 
        super().__init__(name=_name, state=_state, fips=_fips) 

    @model_validator(mode='before')
    @classmethod
    def _ensure_county_in_state(cls, data: dict):   

        required_attrs = ('name', 'state')
        if not all(r in data.keys() for r in required_attrs):
            raise ValueError(f"Must provide both county name and StateUS/state_name") 
        
        state_name = data['state'] if isinstance(data['state'], str) else data['state'].name
        county_name = data['name']

        row_match = COUNTY_LOOKUP_DF.filter(
            pl.col('county_name').eq(county_name) & pl.col('state_name').eq(state_name) 
        ).collect().shape[0]
        if row_match == 0: 
            raise ValueError(f"Provided county and state name not found in lookup table (db.Geographies.countypop)")
        
        return data 

    def lookup(self): 
        """
        Get row of county from the lookup table. 
        """
        return COUNTY_LOOKUP_DF.filter(pl.col('county_name').eq(self.name)
                                       & pl.col('state_name').eq(self.state.name)
                                       & pl.col('county_fips').eq(self.fips.code))
    
    @classmethod 
    def _parse_location_str(cls, s: str, clean_ws: bool = True) -> tuple[str]: 
        """
        Parse <county_name>, <state>, 
        """
        s_parsed = s
        if clean_ws:
            s_parsed = sub('\s+', ' ', s_parsed.strip()) 
        try:
            county_name, state_desig = s_parsed.split(', ')
        except ValueError as e: 
            county_name, state_desig = None, None
            raise ValueError(f"County and state name must be formatted <County_Name>, <State_USPS> ({s_parsed})")
        
        # Determine if valid designation for a state 
        StateUS.det_desig_type(state_desig)

        return county_name, state_desig

    @classmethod
    def from_location_str(cls, s: str, clean_ws: bool = True) -> 'CountyUS': 
        """
        Construct CountyUS() from <county_name>, <state> location string.
        """
        name, state_desig = cls._parse_location_str(s, clean_ws) 
        state = StateUS(state_desig)

        return CountyUS(name=name, state=state)
    
    def __str__(self): 
        return str(LocationString(county_name=self.name, state_usps=self.state.usps))
    
    def to_location_str(self):
        return self.__str__()
    
    def to_record(self) -> LocationRecord: 

        return LocationRecord(county_name=self.name,
                              county_fips=self.fips.code,
                              state_name=self.state.name,
                              state_usps=self.state.usps,
                              state_fips=self.state.fips,
                              location=self.to_location_str())

    def to_records(self) -> list[LocationRecord]: 
        """
        Ensure operator overloading with StateUS
        """
        return [self.to_record()]


    @classmethod
    def from_record(cls, r: LocationRecord) -> 'CountyUS':
        return cls.__init__(name=r.county_name, state=r.state_name)

    @classmethod
    def _lookup_county_fips(cls, county_name: str, state: StateUS) -> CountyFips: 
        """
        Get the county_fips from the GEOG.countypop lookup table.
        """
        county_fips = COUNTY_LOOKUP_DF.select('county_name','state_usps', 'county_fips')\
            .filter(pl.col('state_usps').eq(state.usps) 
                    & pl.col('county_name').eq(county_name))\
            .collect().rows()
        if len(county_fips) == 0: 
            raise ValueError(f"{county_name}, {state.usps} not found in database.")
        return CountyFips(county_fips[0][-1])
    
    @classmethod
    def random(cls, n: int = 1) -> list['CountyUS']:
        rows = COUNTY_LOOKUP_DF\
            .select('county_name', 'state_name')\
            .collect()\
            .sample(n).to_dicts()
        return [CountyUS(name=r['county_name'], 
                        state=StateUS(r['state_name'])) for r in rows]
    ## TODO: Not actually sure if in the R code these columns are meant to be consistent within a single dataframe, or if any contains both. 
        # I know that countyortownName contains fields which aren't in county_name 
    # @model_validator(mode='before')
    # @classmethod
    # def ensure_county_match(cls, data: dict): 
    #     """
    #     Ensure that county_name matches countyortownName
    #     """
    #     if data['countyortownName'] and data['county_name'] \
    #         and (data['countyortownName'] != data['county_name']): 
    #             raise ValueError(f'Fields "county_name" and "countyortownName" do not match.')
    #     return data 

    def __lt__(self, other): 
        return str(self) < str(other)