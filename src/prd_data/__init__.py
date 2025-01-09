"""
## prd_data

A package for distributing the datasets in the Policy Rules Database (PRD) in an accessible format for programmers and data scientists.
Original data comes from the AFRB's [Policy Rules Database GitHub Repository](https://github.com/Research-Division/policy-rules-database).

See `loaders.py` for convenient data loaders to work with the datasets in the package.

---
{file_utils_doc}

"""

import json

import prd_data.file_utils as fu

# import prd_data.loaders as loaders
from prd_data.file_utils import __doc__ as fu_doc
from prd_data.file_utils import (
    get_data_dir,
    list_files,
    make_file_tree_dict,
    print_file_tree,
)

# from prd_data.loaders import __doc__ as loaders_doc

__doc__ = __doc__.format(
    file_utils_doc=fu_doc,
    # loaders_doc=loaders_doc
)

if __name__ == "__main__":
    print(__doc__)
