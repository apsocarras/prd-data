### prd-data 

Package containing source data for the Policy Rules Database (PRD). 

We separated the data storage and loading from the prd-calculator package (which has this as a dependency.)

See setup.py + MANIFEST.in for how to include files in your package wheel and source ([video](https://www.youtube.com/watch?v=bfyIrX4_yL8))
* Recommend to follow along first and then use [uv build](https://docs.astral.sh/uv/)

To push the zipped parquets to this remote, I had to use SSH instead of HTTPS. I ran the following commands: 
* git config --global http.postBuffer 524288000
* git config --global http.sslVerify false (temporary)
* git remote set-url origin git@github.com:apsocarras/prd-data.git

Confirm your SSH key is set up with ssh -T git@github.com