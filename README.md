# cloud_pricing
Fetches EC2 specs &amp; pricing, specifically for Redpanda BYOC


## AWS

Run `aws_pricing.py`, which will generate aabout 2k lines of csv output.   Copy this and paste into the Ubercalc: 
* Tab: `AWS_Reference`
* Cell: `A6`

  This will paste everything into column A.   Note near the bottom of the screen is a clipboard with a dropdown.   Select split text to columns and everything will move to the correct column in the reference sheet.



## GCP

There are two flavors of GCP pricing, I've included both because they use wildlly different techniques to get the data.  


### The better way

This uses some GCP python libraries to authenticate, but there is no client library to get pricing info (`google-cloud-billing` is the closest thing I could find).   Instead, it uses the same REST endpoint but gets all the skus & info about those skus in a single (paginated) call.   The output is a sorted csv list of the VMs & SSD pricing by region.  Paste that csv into the Ubercalc:
* Tab: `GCP_Reference`
* Cell: `A20`

  This will paste everything into column A.   Note near the bottom of the screen is a clipboard with a dropdown.   Select split text to columns and everything will move to the correct column in the reference sheet.


### The old way

The deprecated version is `gpc_pricing_scrape.py` which iterates over many pages in the GCP docs to cobble together enough information to get the pricing.   It's fragile, and their overall setup doesn't lend itself well to a programmatic approach.   But it works, as of this commit.   The only hard requirement is that you'll need an API Key from GCP, but that is easy to set up.

In this version the SSD pricing is separated from the VM pricing, which reflects a prior version of the ubercalc for GCP pricing. 

