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



### The old way

The deprecated version is `gpc_pricing_scrape.py` which iterates over many pages in the GCP docs to cobble together enough information to get the pricing.   It's fragile, and their overall setup doesn't lend itself well to a programmatic approach.   But it works, as of this commit.   The only hard requirement is that you'll need an API Key from GCP, but that is easy to set up.

In this version the SSD pricing is separated from the VM pricing, which reflects a prior version of the ubercalc for GCP pricing. 

