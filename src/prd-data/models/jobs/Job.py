from ....config import *
from .... import logging_config
import logging
from .OccupationOEWS import OccupationOEWS
from ....funcs.utils import combine_dicts
from ....funcs.decorators import abridge_repr


# @abridge_repr    
class Job(OccupationOEWS): 
    """
    Model for someone's current job situation by attaching other variables to an OEWS occupation. 
    """
    hours: Optional[int] = pyd.Field(default=40, description="Number of hours worked per week (round to nearest whole number).", gt=0, le=100)
    wage_hourly: Optional[float] = pyd.Field(None, description="Hourly wage.", gt=0, le=100)
    experience: Optional[int] = pyd.Field(0, description="Previous years of relevant experience (including in current job title).", ge=0)
    year_started: Optional[int] = pyd.Field(None, description="Year first started in the job (can be in the future)", ge=1950)
    year_ended: Optional[int] = pyd.Field(None, description="Year first started in the job (can be in the future)", ge=1950)
    
    # def __init__(self, 
    #          occ_code: Optional[str],
    #          occ_title: Optional[str],
    #          hours: Optional[int],
    #          hourly_wage: Optional[float],
    #          experience: Optional[int],
    #          year_started: Optional[int],
    #          year_ended: Optional[int],
    #          ): # since I gave OccupationOEWS a custom init it seems I have to give this one one. 
        
    #     occupation_data = self.lookup(occ_code)
    #     self.hours = hours 
    #     self.wage_hourly = hourly_wage
    #     self.experience = experience
    #     self.year_started = year_started
    #     self.year_ended = year_ended

    #     super().__init__({**dict(occupation_data)}) # throwing errors with Pydantic

    @model_validator(mode='before')
    @classmethod
    def ensure_start_end_year(cls, data: dict): 
        """
        Ensure that if one of year_started or year_ended is provided, both are.
        """
        if bool(data.get('year_started', False)) != bool(data.get('year_ended', False)):
            raise ValueError(f"Must provide both year_started & year_ended or neither.")
        elif data.get('year_ended') and data.get('year_started'):
            if data.get('year_ended') < data.get('year_started'):
                raise ValueError(f'"year_started" must precede year_ended')

        return data 

    def __lt__(self, other):
        """
        Custom less-than operator for placing Jobs in a Sequence (e.g. in CareerPathInput.career_timeline). 
        """  
        return (self.year_ended < other.year_started) or (self.occ_title < other.occ_title)    
    
    def __str__(self):
        out_str = super().__str__()
        if self.wage_hourly:
            out_str += f" (${self.wage_hourly}/hr)" 
        if self.year_started and self.year_ended: 
            out_str += f" (Years: {self.year_started}-{self.year_ended})"
        return out_str
    
    @property
    def start_end(self) -> range: 
        return range(self.year_started, self.year_ended+1)

    @classmethod
    def _validate_kwargs(cls, **kwargs): 
        """
        Validate key word arguments as applying to the model, without actually instantiating a model instance.
        """
        dummy_job = "11-1011" # CEOs 
        Job(occ_code=dummy_job, **kwargs)
        
    def to_record(self, exclude: Sequence = {'year', 'experience'}, drop_none=True) -> 'JobRecord': 

        jr = JobRecord(**{k:getattr(self, k) 
            for k in get_type_hints(JobRecord).keys()
            if k not in exclude and (getattr(self, k) is not None or not drop_none)})
        
        return jr 
    
    def to_records(self, exclude: Sequence = {'year', 'experience'}, drop_none=True) -> list['JobRecord']:
        jr = self.to_record(exclude, drop_none)
        return [JobRecord(**combine_dicts(jr, {'year':y, 'experience':self.experience + (y - self.year_started)}))
                for y in self.start_end]
        
class JobRecord(TypedDict):
    """
    Record with fields used to generate DataFrames     
    """
    occ_code: str
    occ_title: str
    year: int 
    starting_wage: float
    education_duration: int
    experience: int 
    wage_hourly: float
    hours: int 
    empl_healthcare: bool
