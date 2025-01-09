"""
List of all datasets in the database
(TODO: generate JSON programmatically from the listing functions in prd_data.__init__.py during the build step)
(TODO: dump this JSON into this file)
"""

# Do not alter
_FILE_TREE = {
    "geog": {
        "files": [
            "statemap.parquet",
            "countypop.parquet",
            "msamap.parquet",
            "TowntoWorkforceDevAreaMap.parquet",
        ]
    },
    "expenses": {
        "files": [
            "food_schoolMeals.parquet",
            "food_WIC.parquet",
            "healthcare_ALICE.parquet",
            "employerHealthcare.parquet",
            "transportation_ALICE.parquet",
            "healthcare_healthexchange.parquet",
            "childcare_ALICE.parquet",
            "healthcare_Medicaid.parquet",
            "providercost_NV.parquet",
            "housing.parquet",
            "providercost_VT.parquet",
            "food_USDA.parquet",
            "tech_ALICE.parquet",
        ]
    },
    "parameter_defaults": {"files": ["parameter_defaults.parquet"]},
    "taxes": {
        "files": [
            "fedinctax.parquet",
            "ficatax.parquet",
            "localinctax.parquet",
            "salestax.parquet",
            "stateinctax.parquet",
        ]
    },
    "benefits": {
        "healthcare": {
            "files": [
                "medicareStateDate.parquet",
                "medicaid.parquet",
                "aca.parquet",
                "medicareMaritalstat.parquet",
            ]
        },
        "housing": {"files": ["liheap.parquet", "section8.parquet"]},
        "tax_credits": {
            "files": [
                "fedeitc.parquet",
                "statectc.parquet",
                "statecdctc.parquet",
                "fedcdctc.parquet",
                "stateeitc.parquet",
                "fedctc.parquet",
            ]
        },
        "social_security": {"files": ["ssdi.parquet", "ssi.parquet", "ssp.parquet"]},
        "childcare": {
            "files": [
                "ccdf_AK.parquet",
                "ccdf_WY.parquet",
                "ccdf_MI.parquet",
                "ccdf_ID.parquet",
                "ccdf_GA.parquet",
                "ccdf_RI.parquet",
                "ccdf_OR.parquet",
                "ccdf_MT.parquet",
                "ccdf_MA.parquet",
                "ccdf_LA.parquet",
                "ccdf_IL.parquet",
                "ccdf_NE.parquet",
                "ccdf_DE.parquet",
                "ccdf_IN.parquet",
                "ccdf_NY.parquet",
                "ccdf_NM.parquet",
                "ccdf_SC.parquet",
                "ccdf_UT.parquet",
                "ccdf_CO.parquet",
                "ccdf_ND.parquet",
                "ccdf_TX.parquet",
                "ccdf_KY.parquet",
                "ccdf_MN.parquet",
                "ccdf_OH.parquet",
                "ccdf_NH.parquet",
                "ccdf_AL.parquet",
                "ccdf_MS.parquet",
                "ccdf_PA.parquet",
                "ccdf_MO.parquet",
                "ccdf_WV.parquet",
                "ccdf_HI.parquet",
                "ccdf_OK.parquet",
                "ccdf_AZ.parquet",
                "ccdf_MD.parquet",
                "ccdf_KS.parquet",
                "ccdf_TN.parquet",
                "ccdf_VT.parquet",
                "ccdf_WA.parquet",
                "ccdf_VA.parquet",
                "ccdf_NC.parquet",
                "ccdf_NV.parquet",
                "ccdf_IA.parquet",
                "ccdf_AR.parquet",
                "ccdf_CA.parquet",
                "ccdf_SD.parquet",
                "ccdf_NJ.parquet",
                "ccdf_CT.parquet",
                "ccdf_DC.parquet",
                "ccdf_WI.parquet",
                "ccdf_FL.parquet",
                "ccdf_ME.parquet",
            ]
        },
        "food": {
            "files": [
                "wic.parquet",
                "tanf.parquet",
                "schoolmeal.parquet",
                "snap.parquet",
            ]
        },
    },
    "jobs": {
        "files": [
            "missingEstimates.parquet",
            "fpl.parquet",
            "minWage.parquet",
            "wages.parquet",
            "eduattainment.parquet",
            "smi.parquet",
        ]
    },
}


def get_file_tree():
    return _FILE_TREE
