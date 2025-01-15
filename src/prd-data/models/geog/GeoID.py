from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...._typing import *

from ....config import * 
from .... import logging_config
import logging 

from .FipsCode import StateFips, CountyFips

logger = logging.getLogger(__name__)

class GEOID(BaseModel):
    """
    Model for constructing/validating a complete GEOID (i.e. compose the individual FIPS codes for all specified geography levels).
    https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html

        - Usage: str(GEOID(state_fips, county_fips)) or GEOID(state_fips, county_fips).to_str()
    """
    state_fips: Optional[Union[str, StateFips]]
    county_fips: Optional[Union[str, CountyFips]]

    @classmethod
    def construct_subclass(cls, geog_type: str):
        """
        TODO: Construct a Pydantic model for specific type of GEOID.
        """
    
    # def to_str(self):
    #     return self.__str__() 

    # def __str__(self) -> str: 
    #     """
    #     String representation of the GEOID. Output depends on which fields were provided. 
    #     """
    #     for field_name, field_value in self: 

    #     return