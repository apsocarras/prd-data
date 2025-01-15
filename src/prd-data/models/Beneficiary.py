from ...config import *
from pydantic import Field

from math import floor

# other schemas 
from ..schemas.geog.CountyUS import CountyUS 
from ..schemas.geog.StateUS import StateUS
from ..schemas.jobs.Job import Job 
from ..schemas.jobs.CareerPath import CareerPath
from ..schemas.pa_custom_checks import ensure_enough_locations
from ..schemas.pa_column_schemas import SharedFields as sf 



from .Budget import Budget


class FamilyMember(BaseModel): 
    """
    Data model for a family member in a household on benefits. Used in schemas.beneficiary.BeneficiaryProfile.
    """
    name: Optional[str] = Field(None, description="(Optional) Name of the family member; default is set to <adult|child>_<rank>, if rank is provided.")
    rank: Optional[int] = Field(None, description="(Optional) The 'numeric position' of the family member (1-12; adults 1-6, children 7-12)")
    age: int = Field(..., description="Age of the family member (rounds down to nearest int)", gt=0, lt=130) 
    disability: bool = Field(False, description="Whether or not the family member has a disability")

class Child(FamilyMember): 
    """
    Data model for attributes pertaining to a single child in a household 
    """
    age: ChildAge = Field(..., description="Age of the child (18 or under)", gte=0, lt=18) 

class Adult(FamilyMember): 
    """
    Data model for attributes pertaining to a single adult in a household 
    """
    age: AdultAge = Field(..., description="Age of the adult (over 18)", gt=18, lt=130) 
    blind: bool = Field(False, description="Whether the family member is legally blind")
    married: bool = Field(False, description="Whether the adult is married.")
    prev_ssi: bool = Field(False, description="Whether the adult has previously received Supplemental Security Income (SSI).")  

    ## Current Insurance/benefits  
    ssdiPIA: float = Field(0, description="The primary insurance amount (PIA) of SSDI benefits paid to the adult, if any.", gte=0)

    ## Employment    
    employed: bool = Field(..., description="Whether the adult is employed.")
    current_job: Optional[Job] =  Field(None, description="Current job of the adult. May differ from current job in career_path (e.g. if modeling an alternative or potential path).")
    career_path: Optional[CareerPath] = Field(None, description='Sequence of past, current, and/or future jobs. May represent actual or potential career trajectory.')

    earned_income: Optional[Union[int, float]] = Field(None, description="Annual earned income for the adult.", gte=0)
    income_child_support: Optional[NonNegativeNumber] = Field(None, description="Individual income from child support.")
    income_investment: Optional[NonNegativeNumber] = Field(None, description="Individual income from investments.")
    income_gift: Optional[NonNegativeNumber] = Field(None, description="Income from gifts.")
    income_other: Optional[NonNegativeNumber] = Field(None, description="Income from other sources.")    

    ## Expenses 
    disab_work_exp: Optional[NonNegativeNumber] = Field(None, description="Expenses required for the adult to work.")

    ## Tax filing 
    filing_status: Literal['individual', 'married_filing_jointly', 'heads_of_household', 'married_filing_separately'] = Field(..., description="Filing status of the individual in the household.")
    age_spouse: Optional[int] = Field(None, description="Age of spouse (if applicable)") # TODO: THis is bizarre w/o context -- you need to leave a note explaining why you included a certain field.
    
    @property
    def empl_healthcare(self): 
        if self.current_job: 
            return self.current_job.get("empl_healthcare", None)
        else: # should be 
            return None

    @model_validator('after')
    @classmethod
    def ensure_job_employed(cls, data: dict) -> None: 
        """
        Check that the 'employed' flag agrees with the job parameter 
        """
        if not data['employed'] and data['job'] is not None: 
            raise ValueError(f'"employed" flag is set to false but job is not ({data["job"].occ_title})') 
        elif data['employed'] and not data['job']:
            raise ValueError(f'Must specify job if employed (can use a placeholder job)')
    
    
    @model_validator('after')
    @classmethod
    def ensure_disabled_ssdiPIA(cls, data:dict) -> None: 
        """
        (TO-DO): Check that adult is disabled if they are receiving SSDI.
        """
        return 
    
    @model_validator('after')
    @classmethod
    def ensure_disabled_disab_work_exp(cls, data:dict) -> None: 
        """
        (TO-DO): Check that adult is disabled if disab_work_exp != 0.
        """
        return 

    @model_validator('after')
    @classmethod
    def ensure_income(cls, data:dict) -> None: 
        """
        (TO-DO): Check that the income variables agree 
        """
        return 
    
class BeneficiaryProfile(BaseModel): 
    """
    Data model for the household/beneficiary profile with shared attributes. 
    Can set multiple income levels and county locations for conducting comparisons.
    """
    # Other variables
    location: Union[Literal['all'], Sequence[CountyUS], CountyUS, Sequence[StateUS], StateUS] = Field(..., description="County (or State) of residence (can input multiple counties/states for comparisons, or 'all' for all counties).", min_length=1) 
    
    # Members
    adults: Sequence[Adult] = Field(..., description="Adults in the household.", min_length=1, max_length=6)
    children: Sequence[Child] = Field(..., description="Children in the household.", min_length=1, max_length=6)
    
    # Income & Expenses
    income_levels: Optional[Union[NonNegativeNumber, Sequence[NonNegativeNumber]]] = Field(None, description="Total income for the family to compare in a point of time (can give multiple values to see a range).", min_length=1)
    budget: Optional[Union[Budget, Sequence[Budget]]] = Field(None, description="(Annual or monthly) Household expenses and income (optionally by year)") 

    # Assets 
    assets_cash: float = 0
    assets_car: float = 0 
    
    
    @property
    def earned_income(self): 
        """
        Sum total income from employment from all adults in the family 
        """
        return sum(a.earned_income for a in self.adults)
    
    @property
    def married_adults(self) -> tuple: 
        """
        List the married adults in the family.
        """
        return tuple(a for a in self.adults if a.married)
    
    @property
    def prev_ssi(self) -> tuple: 
        """
        List the adults in the family who have previously received SSI.
        """
        return tuple(a for a in self.adults if a.prev_ssi)

    @property
    def empl_healthcare(self) -> tuple: 
        """
        List the adults in the family who receive healthcare from their employer.
        """
        return tuple(a for a in self.adults if a.empl_healthcare)
     
        
class BeneficiaryCols(TypedDict):
    """
    Core columns for determining eligibility for benefits programs according to the R repo. 
    """
    fam_size: int 
    has_dependent: bool 
    ak_or_hi: bool 
    num_adults: int 
    num_kids: int 
    num_under_13: int 
    age_youngest_child: int 
    total_assets: float 
    filing_status: int # 1: single, 2: head of household, 3: married filing jointly
    uninsured: bool # inverse of empl_healthcare 

class EligibilityCols(pa.DataFrameModel):
    """
    Model to check that a DataFrame contains core eligibility columns. 
    This the baseline for all other benefits functions in the codebase.
    """
    agePerson1: AdultAge = sf.Beneficiary.Eligibility.age(Config.defaults.starting_age) # only agePerson1 is required to not be null
    agePerson2: AdultAge = sf.Beneficiary.Eligibility.age() 
    agePerson3: AdultAge = sf.Beneficiary.Eligibility.age()
    agePerson4: AdultAge = sf.Beneficiary.Eligibility.age()
    agePerson5: AdultAge = sf.Beneficiary.Eligibility.age()
    agePerson6: AdultAge = sf.Beneficiary.Eligibility.age()
    agePerson7: ChildAge = sf.Beneficiary.Eligibility.age() 
    agePerson8: ChildAge = sf.Beneficiary.Eligibility.age()
    agePerson9: ChildAge = sf.Beneficiary.Eligibility.age()
    agePerson10: ChildAge = sf.Beneficiary.Eligibility.age()
    agePerson11: ChildAge = sf.Beneficiary.Eligibility.age()
    agePerson12: ChildAge = sf.Beneficiary.Eligibility.age()
    
    # Locations
    state_name: StateName = sf.Geo.state_name()
    state_fips: StateFipsType = sf.Geo.state_fips()
    state_usps: StateUSPS = sf.Geo.state_usps()
    county_name: str = sf.Geo.county_name()
    county_fips: str = sf.Geo.county_fips()
    location: str = sf.Geo.location()

    # Calculated from core columns 
    fam_size: int 
    num_adults: int 
    num_kids: int 
    num_under_13: int 
    has_dependent: bool 
    age_youngest_child: int 
    ak_or_hi: Literal['AK',"HI", None] 
    assets_car: float 
    assets_cash: float 
    total_assets: float # car and cash 
    income_child_support: float
    filing_status: int # 1: single, 2: head of household, 3: married filing jointly
    uninsured: bool # inverse of empl_healthcare 
    empl_healthcare: bool 

class IncomeCols(pa.DataFrameModel): 
    income1 = sf.Beneficiary.earned_income()









class BeneficiaryProfileDF(pa.DataFrameModel): 
    """
    DataFrameModel for columns relating to a beneficiary profile's benefits eligibility (family information; location; income; employment status)
    See function.InitialTransformations.

    Specify a family with up to 12 members (6 adults, 6 children)

    Other functions in calc apply columns to this base DataFrame.

    As with other DataFrame schemas, keep columns here mandatory -- specify which can be omitted in inputs/outputs on a per-function basis.
    """

    fam_size: int 
    num_adults: int 
    num_kids: int 
    num_under_13: int 
    has_dependent: bool 
    age_youngest_child: int 
    ak_or_hi: Literal['AK',"HI", None] 
    assets_car: float 
    assets_cash: float 
    total_assets: float # car and cash 
    income_child_support: float
    filing_status: int # 1: single, 2: head of household, 3: married filing jointly
    uninsured: bool # inverse of empl_healthcare 
    empl_healthcare: bool 

    income1: float 
    income2: float
    income3: float
    income4: float
    income5: float
    income6: float

    blind1: bool = sf.Beneficiary.blind()
    blind2: bool = sf.Beneficiary.blind()
    blind3: bool = sf.Beneficiary.blind()
    blind4: bool = sf.Beneficiary.blind()
    blind5: bool = sf.Beneficiary.blind()
    blind6: bool = sf.Beneficiary.blind()

    childcare6: float = sf.Beneficiary.childcare()
    childcare7: float = sf.Beneficiary.childcare()
    childcare8: float = sf.Beneficiary.childcare()
    childcare9: float = sf.Beneficiary.childcare()
    childcare10: float = sf.Beneficiary.childcare()
    childcare11: float = sf.Beneficiary.childcare()
    childcare12: float = sf.Beneficiary.childcare()
    






    class Config:
        ensure_enough_locations()



# \$[a-zA-Z].*(\n|\))
