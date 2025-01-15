from ....config import *
from .... import logging_config
import logging
from ....funcs.decorators import abridge_repr

logger = logging.getLogger(__name__)

from ...db import JOB_LOOKUP_DF

@abridge_repr
class OccupationOEWS(BaseModel):
    """ 
    Model for an occupation listed in the OEWS database (db.JOBS.eduattainment). 

    Optionally attach weekly hours, weekly wage, starting wage, educational requirement, and education duration. 
    TO-DO: Default values will come from tables in db.JOBS (some fields need to be added there).
    """
    occ_code: str = pyd.Field(..., description="Occupation code for job title as listed in the OEWS database.", pattern="[0-9]{2}-[0-9]{4}")
    # occ_title: Optional[str] = pyd.Field(None, description="Job title for the occupation; (omit to avoid) validation against the OEWS database table (db.Jobs.eduattainment)" )
    starting_wage: Optional[float] = pyd.Field(None, description="Hourly wage for job starting with no experience in the given job title. Will override default for a given location from db.Jobs.wages.", gt=0)
    education_duration: Optional[int] = pyd.Field(None, description="Time to earn degree or other training required for Job. See default value in db.Jobs.eduattainment.") 
    education_level: Optional[EducationLevel] = pyd.Field(None, description="Level of education required for the job.")
    
    # Fields not included in the database but which probably should be - may add these later 
    experience_required: Optional[int] = pyd.Field(None, description="Years of experience in related positions typically required to acquire this job title.", gt=0, le=30)
    promotes_from: Optional[Union['OccupationOEWS', Sequence['OccupationOEWS']]] = pyd.Field(None, description='Another occupation(s) title in the OEWS which typically precedes this one.')
    promotes_to: Optional[Union['OccupationOEWS', Sequence['OccupationOEWS']]] = pyd.Field(None, description='Another occupation(s) title in the OEWS which typically follows this one.')
    empl_healthcare: Optional[bool] = pyd.Field(None, description='Whether an employer typically provides health insurance for this job.')

    ## TODO: Writing this custom init works okay on its own, but Pydantic creates issues when subclassing (see Jobs)
    # def __init__(self, 
    #              desig: Optional[str] = None, 
    #              /, 
    #              occ_code: Optional[str] = None, 
    #              occ_title: Optional[str] = None, 
    #              starting_wage: Optional[float] = None, 
    #              education_duration: Optional[int] = None,
    #              education_level: Optional[EducationLevel] = None, 
    #              experience_required:  Optional[int] = None,
    #              promotes_from: Optional[Union['OccupationOEWS', Sequence['OccupationOEWS']]] = None, 
    #              promotes_to: Optional[Union['OccupationOEWS', Sequence['OccupationOEWS']]] = None, 
    #              empl_healthcare: Optional[bool] = None): 

    #             # Pre-init: check if desig is a valid occ_code or title 
    #             if desig is not None: 
    #                 row_data = self.lookup(desig)
    #             elif occ_code:  
    #                 row_data = self.lookup(occ_code)
    #             elif occ_title: 
    #                 row_data = self.lookup(occ_title)
    #             else: 
    #                 raise ValueError(f"Must provide valid occupation code or title.")
            
    #             for attr, attr_str in zip((occ_code, occ_title, education_duration, education_level, 
    #                         starting_wage, experience_required, promotes_to, promotes_from, empl_healthcare),
    #                     ('occ_code', 'occ_title', 'education_duration', 'education_level', 
    #                         'starting_wage', 'experience_required', 'promotes_to', 'promotes_from', 'empl_healthcare')):
    #                 if attr_str == 'education_duration': 
    #                     # check for alternative spelling (TODO: remove from source data and double check)
    #                     if educationDuration := row_data.pop('educationDuration', None): 
    #                         row_data['education_duration'] = education_duration if education_duration else educationDuration
    #                     else: 
    #                         def_value = row_data.get('education_duration', None)
    #                         row_data['education_duration'] = education_duration if education_duration else def_value
    #                 else:
    #                     row_data[attr_str] = attr if attr else row_data.get(attr_str, None)

    #             super().__init__(**row_data)


    @classmethod
    def lookup(cls, desig: str ) -> dict: 
        df = JOB_LOOKUP_DF.filter(pl.col('occ_code').eq(desig) | pl.col('occ_title').eq(desig))
        if df.collect().is_empty():  
            raise ValueError(f"Must provide valid occ_code or occ_title ({desig})")
        return df.collect().to_dicts()[0]

    @field_validator('occ_code')
    @classmethod 
    def ensure_code_in_db(cls, v: Any):
        """
        Check that the Job code is located in the OEWS database.
        """
        if JOB_LOOKUP_DF.filter(pl.col('occ_code').eq(v)).collect().is_empty():
            raise ValueError(f'{v} not a recognized occupation code in the OEWS database.')
        return v 

    # @field_validator('occ_title')
    # @classmethod 
    # def ensure_title_in_db(cls, v: Any):
    #     """
    #     Check the OEWS database for agreement between the provided job title and occupation code.
    #     """ 
    #     if JOB_LOOKUP_DF.filter(pl.col('occ_title').eq(v)).collect().is_empty():
    #         raise ValueError(f'Job title "{v}" not a recognized job title in the OEWS database.')
    #     return v 

    # @model_validator(mode='before')
    # @classmethod 
    # def ensure_code_title_match(cls, data: dict):
    #     """
    #     Check the OEWS database for agreement between the provided job title and occupation code.
    #     """ 
    #     if occ_title := data.get('occ_title'): 
    #         if JOB_LOOKUP_DF.filter(pl.col('occ_title').eq(occ_title) &
    #                                   pl.col('occ_code').eq(data.get('occ_code'))).collect().is_empty():
    #             raise ValueError(f'Job title "{occ_title}" does not match the provided job code {data["occ_code"]}')
    #     return data
    
    @property
    def occ_title(self):
        logger.debug("TODO: Add this attribute to the data model before __init__")
        if  not getattr(self, '_occ_title', None):
            self._occ_title = JOB_LOOKUP_DF.filter(pl.col('occ_code').eq(self.occ_code)).select('occ_title').collect().rows()[0][0]
        return self._occ_title
        
    @property
    def test_prop(self): 
        return 'yayes'

    @classmethod
    def random(cls, from_list: Sequence[OEWS_Code] | None = None) -> 'OccupationOEWS':
        """
        Get random occupation from the OEWS database.

        Args: 
            from_list: List of occupation codes to restrict selection (uses full lookup table if None).
        """ 
        lookup = JOB_LOOKUP_DF.filter(pl.col('occ_code').is_in(from_list)) \
        if from_list is not None else JOB_LOOKUP_DF
        
        row_data = lookup.select(['occ_code',
                                'occ_title',  
                                'education_duration',
                                'education_level'
                                ])\
            .collect()\
            .sample(1)\
            .rows()[0]
        return OccupationOEWS(occ_code=row_data[0],
                              occ_title=row_data[1],
                              education_duration=row_data[2], 
                              education_level=row_data[3])
    
    def __str__(self): 
        return f"({self.occ_code}) {self.occ_title}"
    
    # def __repr__(self): 
    #     args = get_type_hints(self).keys()
    #     vals = tuple(getattr(self,k) for k in args)
    #     arg_str = ", ".join(f"'{t[0]}={t[1]}'" for t in zip(args, vals) if t[1])
    #     if any(x is None for x in vals):
    #         arg_str +=  ", ..."
    #     return f"{self.__repr_name__()}({arg_str})"

# OccupationOEWS.model_rebuild() ## UPDATE FORWARD REFERENCES 
