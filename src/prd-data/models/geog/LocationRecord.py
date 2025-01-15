from typing import TypedDict, Optional
from collections import UserString

class LocationString(UserString):
    """
    Optional constructor for creating a string for a county and US state
    """
    county_name: str 
    state_usps: str 
    def __init__(self, s: Optional[str] = None, /, county_name: Optional[str] = None, state_usps: Optional[str] = None):
        if s is not None: 
            super().__init__(s)
        else: 
            location_str = county_name.strip().title() + ", " + state_usps.strip()
            super().__init__(location_str)

class LocationRecord(TypedDict): 
    county_name: str 
    county_fips: str 
    state_name: str 
    state_usps: str 
    state_fips: str 
    location: str 
