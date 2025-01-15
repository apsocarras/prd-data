from ....config import *
from .... import logging_config
import logging
from ...db import COUNTY_LOOKUP_DF

class FipsCode(BaseModel):
    """
    Model for validating an individual US FIPS code by jursidiction level.
    https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html
    
    (TODO: Write a small separate Python package for this and GeoID with all geography types supported).
    
    Args: 
        geog_type: Optionally specify the FIPS code as belonging to a US County or State; if not provided, model will attempt to infer type.

    """
    code: str 
    geog_type: Optional[Literal[
                                'state', 
                                'county',
                                'county_subdivision', 
                                'place', 
                                'census_tract', 
                                'block_group',
                                'block',
                                'congress_district',
                                'state_upper_district',
                                'state_lower_distict', 
                                'zcta']]
    
    @model_validator(mode='before')
    @classmethod   
    def validate_code(cls, data: dict): 
        """
        Validate FIPS code by its location level (county or state) 
        """
        match geog_type := data.get('geog_type'):
            case 'county': 
                cls.validate_county(data['code'])
            case 'state': 
                cls.validate_state(data['code']) 
            case None: 
                # Infer type based on number of characters in code 
                if len(data['code']) <= 2: 
                    cls.validate_state(data['code'])
                else: 
                    cls.validate_county(data['code'])
            case _:
                raise ValueError(f'Unsupported geography type ({data["geog_type"]})') 
        return data 
    
    @classmethod
    def validate_state(cls, s: str) -> None: 
        """
        Validate a FIPS code for a US state
        """        
        if COUNTY_LOOKUP_DF.select('state_fips').filter(pl.col('state_fips').eq(s)).collect().is_empty():
            raise ValueError(f'Invalid State Fips Code {s}')

    @classmethod
    def validate_county(cls, s: str) -> None: 
        """
        Validate a FIPS code for a US county 
        """
        if COUNTY_LOOKUP_DF.select('county_fips').filter(pl.col('county_fips').eq(s)).collect().is_empty():
            raise ValueError(f'Invalid County Fips Code {s}')

    @classmethod
    def construct_subclass(cls, geog_type: str): 
        """
        Construct a Pydantic model for a specific type of FIPS code.  
        """
        class CustomFIPSCodeClass(cls): 
            def __init__(self): 
                super().__init__(self, geog_type=geog_type)
        return CustomFIPSCodeClass

## Dynamically generated classes don't seem to work with type hints
# StateFips = FipsCode.construct_subclass(geog_type='state')
# CountyFips = FipsCode.construct_subclass(geog_type='county')

class StateFips(FipsCode): 
    def __init__(self, code):
        super().__init__(code=code,geog_type='state')
    
class CountyFips(FipsCode):    
    def __init__(self, code):
        super().__init__(code=code,geog_type='county')
