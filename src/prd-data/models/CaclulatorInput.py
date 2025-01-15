from pydantic import BaseModel, field_validator, model_validator, Field
from pydantic import NonNegativeInt, NonNegativeFloat
from typing import Optional, Literal, Union, Any, Sequence, Mapping

# other schemas 
from .Beneficiary import BeneficiaryProfile
from .geog import CountyUS, StateUS

class CalculatorInput(BaseModel): 
    """s
    Inputs for the main calculator function in prd.calc.run.py
    """
    # Configuration Variables
    rule_year: int = Field(2023, description="Year for which to apply rules from the PRD.")
    year: int = Field(2023, description="Year for which to run the calculator.")
    location: Optional[Union[Literal['all'], Sequence[CountyUS], CountyUS, Sequence[StateUS], StateUS]] = Field(None, description="County of residence (can set in addition to BeneficiaryProfile.location).", min_length=1) 

    # Beneficiary/household to run calculator on. 
    beneficiaries: Union[Sequence[BeneficiaryProfile], BeneficiaryProfile] = Field(..., description="One or more BeneficiaryProfiles to run the calculator on.")
    
    # boolean flags
    CHILDCARE: bool = Field(True, description="Whether to include childcare costs in the calculations (should always be true according to global.R)")
    HEALTHCARE: bool = Field(True, description="Whether to include healthcare costs in the calculations (should always be true according to global.R)")
    HEADSTART: bool = Field(True, description="Whether to run headstart calculations.")
    CCDF: bool = Field(True, description="Whether to run CCDF calculations.")
    PREK: bool = Field(True, description="Whether to run CCDF calculations.")
    MEDICAID_ADULT: bool = Field(True, description="Whether to run Adult Medicaid calculations.")
    MEDICAID_CHILD: bool = Field(True, description="Whether to run Child Medicaid calculations.")
    ACA: bool = Field(True, description="Whether to run ACA calculations.")
    SNAP: bool = Field(True, description="Whether to run SNAP calculations.")
    SLP: bool = Field(True, description="Whether to run SLP calculations.")
    WIC: bool = Field(True, description="Whether to run WIC calculations.")
    EITC: bool = Field(True, description="Whether to run EITC calculations.")
    TAXES: bool = Field(True, description="Whether to run tax calculations.")
    CTC: bool = Field(True, description="Whether to run CTC calculations.")
    SSI: bool = Field(True, description="Whether to run SSI calculations.")
    CDCTC: bool = Field(True, description="Whether to run CDCTC calculations.")
    TANF: bool = Field(True, description="Whether to run TANF calculations.")
    SSDI: bool = Field(True, description="Whether to run SSDI calculations.")
    FATES: bool = Field(True, description="Whether to run FATES calculations.")
    
    # Housing Block
    SECTION8: bool = Field(True, description="Whether to run Section 8 calculations.")
    LIHEAP: bool = Field(False, description="Whether to run LIHEAP calculations.")
    RAP: bool = Field(False, description="Whether to run RAP calculations.")
    FRSP: bool = Field(False, description="Whether to run FRSP calculations.")


    @model_validator(mode="before")
    @classmethod
    def ensure_housing(cls, data: dict): 
        """
        Check that the housing parameters are validly configured. 
        """
        housing_programs = ['LIHEAP', 'SECTION8', 'RAP', 'FRSP']
        ctr = 0
        for p in housing_programs: 
            if data[p]: 
                ctr += 1
            if ctr > 2: 
                return ValueError(f'Select only one housing support program: {",".join(housing_programs)}')
            
    @model_validator(mode="before")
    @classmethod
    def ensure_childcare(cls, data: dict): 
        """
        Check that the childcare parameters are validly configured. 
        """
        if data['FATES'] and not data['CCDF']: 
            raise ValueError("FATES requires CCDF")

    