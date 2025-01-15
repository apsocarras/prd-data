from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt
from typing import Optional, Union, ForwardRef
from datetime import date, datetime
from .geog import StateUS, CountyUS


NonNegativeNumber = Union[NonNegativeInt, NonNegativeFloat]

class Taxes(BaseModel): 
    """
    Class for modeling gross and net (i.e. minus credits) taxes owed by a household in a given year and location (excluding sales tax). 
    """ 

    year: int = Field(2024, description="Year tax amounts apply to.", gte=2023)
    state: Optional[StateUS] = Field(None, description="Which state the state income tax is associated with.")
    county: Optional[CountyUS] = Field(None, description="Which county the local income tax is associated with, if any.")
    
    income_tax_fed: NonNegativeNumber = Field(0, description="Federal personal income tax.")
    income_tax_state: NonNegativeNumber = Field(0, description="State personal income tax.")
    income_tax_local: NonNegativeNumber = Field(0, description="Local personal income tax.")
    FICA: NonNegativeNumber = Field(0, description="") 

    credits: Optional[ForwardRef("TaxCredits")] = Field(None, description="Tax credits earned from taxes paid the previous year.")
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        self.tax_liability_fed = max(0, self.income_tax_fed - (self.credits.EITC_fed + self.credits.CDCTC_fed + self.credits.CTC_fed))
        self.net_income_fed = self.income_fed - (self.EITC_fed + self.CDCTC_fed + self.CTC_fed)
        
        
        self.net_income_state = self.income_state - (self.EITC_state + self.CDCTC_state + self.CTC_state)


class TaxCredits(BaseModel): 
    """
    Class for modeling tax credits reducing taxes paid by a household for a given year. 
    """ 
    year: int = Field(2024, description="Year tax credits apply to.", gte=2023)
    state: Optional[StateUS] = Field(None, description="Which state the EITC, CTC, and CDTC is associated with.")
    EITC_fed: NonNegativeNumber = Field(0, description="Federal Earned Income Tax Credit (EITC).", gte=2023)
    EITC_state: NonNegativeNumber = Field(0, description="State Earned Income Tax Credit (EITC).", gte=2023)
    CDCTC_fed: NonNegativeNumber = Field(0, description="Federal Child and Dependent Care Tax Credit (CDCTC)", gte=2023)
    CDCTC_state: NonNegativeNumber = Field(0, description="State Child and Dependent Care Tax Credit (CDCTC)", gte=2023)
    CTC_fed: NonNegativeNumber = Field(0, description="Federal Child Tax Credit (CDCTC)", gte=2023)
    CTC_state: NonNegativeNumber = Field(0, description="State Child Tax Credit (CDCTC)", gte=2023)


    


