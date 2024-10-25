# Building Pricing Tables for Redpanda Ubercalc

Fetches VM specs &amp; pricing, specifically for Redpanda BYOC, but can be made to pull all instances for all regions.

In a perfect world this would automatically push into the google sheet, but the Redpanda google account doesn't want to allow external applications to modify google docs, so we're stuck doing this manually.   The general idea is that you run one of these scripts, then copy/paste the output into the appropriate tab within the Ubercalc.   The output is csv written to stdout.   If you copy that and paste it, it will all go into a single column.   Google Sheets will give you a little icon near the bottom of the screen asking how you want to deal with the delimted data you just pasted in.  The answer is you want to split text to columns.   It will figure out that the comma is your delimiter, and it will push everthing into the next 6 or 7 columns, which is what the Ubercalc fourmulas are expecting.


## AWS

This uses boto3 to get pricing information by instance/region, and I believe makes a call per instance per region.  Not sure if this could be made more efficient with smarter filters, etc.   As-written, the expectaion is that your session will already have authenticated with AWS.  

Run `aws_pricing.py`, which will generate aabout 2k lines of csv output.   Copy this and paste into the Ubercalc: 
* Tab: `AWS_Reference`
* Cell: `A6`

  This will paste everything into column A.   Note near the bottom of the screen is a clipboard with a dropdown.   Select split text to columns and everything will move to the correct column in the reference sheet.

### Maintenance

New instance types & regions should be added to the respective lists found in `regions.py` and `instances.py`.   Pricing will be pulled for all the regions in that list for every instance in that list.  An exclusion list is maintained in `aws_pricing.py` but this is reserved for problematic regions that return weird data.

---

## GCP

There are two flavors of GCP pricing, I've included both because they use wildlly different techniques to get the data.  


### The better way

`gcp_pricing.py`  uses some GCP python libraries to authenticate, but there is no client library to get pricing info (`google-cloud-billing` is the closest thing I could find).   Instead, it uses the same REST endpoint but gets all the skus & info about those skus in a single (paginated) call.   

The output is a sorted csv list of the VMs & SSD pricing by region.  Paste that csv into the Ubercalc:
* Tab: `GCP_Reference`
* Cell: `A20`

  This will paste everything into column A.   Note near the bottom of the screen is a clipboard with a dropdown.   Select split text to columns and everything will move to the correct column in the reference sheet.

  *NOTE*:  you may need to `pip install google-auth`

  The code will look for a credentials key file, which you can download when you create a service acct in GCP.  The file will look like this.  It's not like a pem file, you don't need special permissions to use it.  Just make sure your python app can read the file.

  ```json
  {
  "type": "service_account",
  "project_id": "cnelson-387114",
  "private_key_id": "<your priviate key id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADAN...blah blah blah...veGRz7GChmx/dk=\n-----END PRIVATE KEY-----\n",
  "client_email": "ubercalc-pricing-info@yourProjectID.iam.gserviceaccount.com",
  "client_id": "your client id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ubercalc-pricing-info%40yourProjectID.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
  }
  ```


#### Maintenance

New instance types/families will need to be added to the `gcp_instance` list found in `instances.py`.  Note the name might not be what you think it is, but how to precisely find that requires some brute force.
TODO:  write a module to show the possible instance type names

New regions that come up will cause the app to throw an error, instucting you to add the new region to the `gcp_region_defs` list found in `regions.py`.   There is no way around this at this time.


### The old way

The _deprecated_ version is `gpc_pricing_scrape.py` which iterates over many pages in the GCP docs using Beautiful Soup to cobble together enough information to get the pricing.   It's fragile, and their overall setup doesn't lend itself well to a programmatic approach.   But it works, as of this commit.   The only hard requirement is that you'll need an API Key from GCP, but that is easy to set up.

In this version the SSD pricing is separated from the VM pricing, which reflects a prior version of the ubercalc for GCP pricing. 

---

## Azure

Azure is the simplest of the cloud providers as it uses a public API to get the instance pricing.   Azure appears to have several layers of savings, the typical 1 & 3 year Reserved pricing but also 1 & 3 year "savings plans."   You can find these from their docs, but the API only seems to return the RI & On Demand pricing (also Spot & others that we don't care about).  It does this with a single (paginated) call, so there is no real concern about throttling API usage etc.

Run `azure_pricing.py`, which will generate ~1000 lines of csv output.  Copy and paste this into the Ubercalc:
* Tab: `Azure_Reference`
* Cell: Currently `A91`, but soon `A5`

  This will paste everything into column A.   Note near the bottom of the screen is a clipboard with a dropdown.   Select split text to columns and everything will move to the correct column in the reference sheet.


### Maintenance

* if you need to add a new specific instance type (i.e. they have added an `L192as_v3`), just add that specific instance type to the `instances` array inside the `azure_instance` list found in `instances.py`.

* If you need to add a whole new family, you'll have to add the new structure to the `azure_instances` list.  You'll also need to figure out what the query extension needs to be.  I don't have a good method for doing that at this time.

* The assumption is that you will want to pull the pricing for every region.  But you may find that you don't need _all_ of them.   Example is the connector instances that BYOC uses.   You're only going to be using those instances in conjunction with BYOC, so only regions where BYOC is deployed is a reasonable filter.   By default, ALL regions will be pulled, but if the `regions` list is populated then only those regions will be pulled.  There is no explicit exclude mechanism.
