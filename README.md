### prd-data 

Package containing source data for the Policy Rules Database (PRD). 

We separated the data storage and loading from the prd-calculator package (which has this as a dependency.)

See setup.py + MANIFEST.in for how to include files in your package wheel and source ([video](https://www.youtube.com/watch?v=bfyIrX4_yL8))
* Recommend to follow along first and then use [uv build](https://docs.astral.sh/uv/)

To push the zipped parquets to this remote, I had to use SSH instead of HTTPS and work around the remote timing out. I ran the following commands: 

```bash
git config --global http.postBuffer 524288000
git config --global http.sslVerify false # (temporary)
git remote set-url origin git@github.com:apsocarras/prd-data.git
git config --global http.sslVerify true 
```
You can confirm your SSH key is set up with `ssh -T git@github.com`

#### Installation 

```bash 
uv pip install prd-data
```
(You should be using [uv](https://docs.astral.sh/uv/)!)

#### The Data 

The source data for this project comes from the Atlanta Federal Reserve Bank's [PRD repository](https://github.com/jdebacker/policy-rules-database), where it lives as R dataframes compressed into `.rdata` files (and now `.xlsx` files, as of 12/13/24).

I kept the original R parameter names but reorganized the data into folders by topic:

```bash 
data/parquet/
├── benefits
├── expenses
├── geog
├── jobs
├── parameter_defaults
└── taxes
```
Running the build step of this package will unzip this directory tree contained in `data.parquet.zip` (see `data_tree.txt` for full contents).

#### The Data Models 

The main goal of distributing the data this way is to improve ease of use for exploratory analysis and incorporation into other packages and projects. 


