import pandera.polars as pa 
from functools import partial 
from ...config import Config
from typing import Literal

class SharedFields():
    """
    Store shared Pandera column fields common across DataFrameModels of different types.
    (See: https://pandera.readthedocs.io/en/stable/dataframe_models.html under "reusing field objects")
    """
    Year = partial(pa.Field, ge=2023, nullable=Config.defaults.nullable)
    YearKey = partial(pa.Field, description="Column for matching closest year of rules to years available in the DataFrame.", nullable=Config.defaults.nullable)
   
    class Jobs: 
        """
        Store shared Pandera column fields for working with jobs data.
        """
        occ_code = partial(pa.Field, description="Occupation code for job title as listed in the OEWS database.", nullable=Config.defaults.nullable)
        occ_title = partial(pa.Field, description="Job title for the occupation; (omit to avoid) validation against the OEWS database table (db.Jobs.eduattainment)", nullable=Config.defaults.nullable)
        education_duration = partial(pa.Field, description="Years to complete degree or other training required for job. See default value in db.Jobs.eduattainment.", gt=0, lt=10, nullable=Config.defaults.nullable)
        starting_wage = partial(pa.Field, description="Hourly wage for job starting with no experience in the given job title. Will override default calculations for a given location based on db.Jobs.wages.", gt=0, nullable=Config.defaults.nullable)        
        empl_healthcare = partial(pa.Field, description="Whether the job provides healthcare.", nullable=Config.defaults.nullable)
        hours = partial(pa.Field, default=40, description="Hours worked per week (default is 40).", ge=0, lt=120, nullable=Config.defaults.nullable)
        experience = partial(pa.Field, default=0, ge=0, description="Years of related past experience (including in current job title).", nullable=Config.defaults.nullable)
    
    class Geo: 
        """
        Store shared Pandera column fields for working with geographical data.
        """
        state_name = partial(pa.Field)
        state_fips = partial(pa.Field)
        state_usps = partial(pa.Field)
        
        county_name = partial(pa.Field)
        county_fips = partial(pa.Field)
        county_or_town_name = partial(pa.Field, description='Name of the county or town.', nullable=Config.defaults.nullable)
        town_fips = partial(pa.Field, description='FIPS code of a US town (native column in R repo.)', nullable=Config.defaults.nullable)
        location = partial(pa.Field, description="Location string formatted '<County_Name>, <State_USPS>'", nullable=Config.defaults.nullable)

        stcountyfips2010 = partial(pa.Field, description="2010 State and county fips separated by '_' (native column in R repo). Seems to accord with county_fips.", nullable=Config.defaults.nullable)

        # This WILL have some nulls, need to catch these alerts. 
        MSA = partial(pa.Field, description="Metropolitan Statistical Area (MSA) looked up from db.Geographies.msamap", nullable=Config.defaults.nullable)
        MSA_replaced_w_state = partial(pa.Field, description="Boolean flag for whether the MSA had to be replaced by the state value (if MSA+occ_title is in db.Jobs.missingEstimates)", nullable=Config.defaults.nullable)  

    class Beneficiary: 

        class Eligibility: 
            """
            Core demographic columns for eligibility.
            """
            age = partial(pa.Field, description="Age of the person in the family.", ge=0, lt=130)
            blind = partial(pa.Field, description="Whether an adult (person1-6) is blind. Note there are no rules in place for blind children, apparently.")
            disability = partial(pa.Field, description="Whether the given family member (person1-12) is blind")
            
            num_under_13 = partial(pa.Field)
            num_adults: int 
            num_kids: int 

            has_dependent: bool 
            age_youngest_child: int 

            filing_status: Literal[1,2,3] = partial(pa.Field, description="1: single, 2: head of household, 3: married filing jointly")
            uninsured: bool 
            empl_healthcare: bool 

            is_citizen: bool 
             
        class Income:
            ann_earned_income = partial(pa.Field, description="Annual earned income associated with the family member (person1-12).")
            monthly_earned_income = partial(pa.Field, description="Monthly earned income associated with the family member (person1-12).")
            ann_unearned_income = partial(pa.Field, description="Annual unearned income associated with the family member (person1-12).")
            monthly_unearned_income = partial(pa.Field, description="Monthly unearned income associated with the family member (person1-12).")

            income_child_support = partial(pa.Field)

            income_bin = partial(pa.Field, description='What income bin a given state would assign to the beneficiary based on their income.')

        class Expenses:
            childcare = partial(pa.Field, description="Childcare cost associated with a child (person6-12).")

        class Assets: 
            total_assets: float 
            assets_car: float 
            assets_cash: float 
