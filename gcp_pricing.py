import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from alive_progress import alive_bar
from regions import gcp_region_defs
from instances import gcp_instances


def clientSetup():
    # Path to your service account key file
    key_file_path = "./ubercalc_creds.json"

    # Create credentials using the service account key
    scopes = ["https://www.googleapis.com/auth/cloud-billing"]
    credentials = service_account.Credentials.from_service_account_file(key_file_path, scopes=scopes)

    # Refresh the token to ensure it's valid
    credentials.refresh(Request())
    access_token = credentials.token

    return access_token


def translateCommit(rawCommit):
    # The commit type text must match what is in the dropdown within the Ubercalc
    # That can be set to whatever, but this decoding represents how it shows in the sheet

    if rawCommit == 'OnDemand':
        return 'On Demand'

    elif rawCommit == 'Commit1Yr':
        return '1 Year Commit'

    elif rawCommit == 'Commit3Yr':
        return '3 Year Commit'


def lookupMissingRegion(region, fullDescription):
    # The region code may not be in the region_defs lookup
    # if you run into one that isn't it's best to add it manually to the region_defs dict
    # and that's why we raise missing ones as an exception

    try:
        # have to do a reverse lookup because the dict is inverted from how we actually need it.  Sue me.
        region_name = list(gcp_region_defs.keys())[list(gcp_region_defs.values()).index(region)]

        return region_name

    except ValueError:
        print(f'Region missing from region_defs dict:  {region}: full description= ', fullDescription)

        # TODO actually add the region code/name to a lookup.
        raise


def translate_instance_class(sku_description, instance_family):

    # Translating the SSD is not required; it just makes the LocalSSD rows show up with an "instance type"
    # so they don't appear out of place when this data gets imported into the Ubercalc

    # Stripping off the "AMD" from 'N2D AMD' is necessary, however.
    # I anticipate other instance types will suffer from this same problem

    if 'SSD' in sku_description:
        return '<local ssd>'

    elif 'AMD' in sku_description:
        # this might end up being fragile, blame Google
        return instance_family.replace('AMD', '').strip()

    else:
        return instance_family


def get_vm_pricing():

    # Service ID for Compute Engine
    service_id = "6F81-5844-456A"  # Service ID for Compute Engine
    pricing_url = f"https://cloudbilling.googleapis.com/v1/services/{service_id}/skus"

    access_token = clientSetup()

    vm_attribs = []

    page_token = None

    with alive_bar(title='Fetching data from Google...', spinner='dots') as bar:
        while True:
            bar()

            params = {}
            if page_token:
                params['pageToken'] = page_token

            # Make a GET request to the pricing API
            response = requests.get(pricing_url, headers={"Authorization": f"Bearer {access_token}"}, params=params)

            if response.status_code == 200:
                pricing_info = response.json()

                for sku in pricing_info.get("skus", []):
                    #print(sku)

                    for instance_family in gcp_instances:

                        if (f'{instance_family} Instance Core' in sku['description'] or
                                f'Commitment v1: {instance_family} Cpu' in sku['description'] or
                                f'{instance_family} Instance Ram' in sku['description'] or
                                f'Commitment v1: {instance_family} Ram' in sku['description'] or
                                'SSD backed Local Storage' in sku['description'] or
                                'Commitment v1: Local SSD' in sku['description']
                                 ) and \
                                'Preemptible' not in sku['description']:

                            commit = translateCommit(sku['category']['usageType'])

                            # some cases have multiple regions attached to a single SKU, so this explodes that to a line per region
                            for region in sku['serviceRegions']:
                                region_name = lookupMissingRegion(region, sku['description'])

                                attrib = [region,
                                          region_name,
                                          translate_instance_class(sku['description'], instance_family),
                                          '', # placeholder--required
                                          '', # placeholder--required
                                          str(sku['pricingInfo'][0]['pricingExpression']['tieredRates'][0]['unitPrice']['nanos'] / 1000000000),
                                          sku['category']['resourceGroup'],
                                          commit,
                                        ]

                                vm_attribs.append(attrib)

                        # troubleshooting block
                        # if you need a new instance type, put it here and see what tweaks you need to make
                        elif 'N2 ' in sku['description']:
                            pass
                            #print(sku)

                        # troubleshooting block
                        # sometimes new regions will show up, add the name here to see what tweaks you need to make
                        elif sku['serviceRegions'][0] == 'me-central1':
                            pass
                            #print(sku)

                        # if you're missing rows, they might be falling through the if statement.  Uncomment the print
                        else:
                            pass
                            #print(sku)

                page_token = pricing_info.get("nextPageToken")
                if not page_token:
                    break

            else:
                print(f"Failed to fetch pricing information: {response.status_code}, {response.text}")


    # deduping is required because the SSD's get added to the list for each instance family
    deduped_list = []
    for i in vm_attribs:
        if i not in deduped_list:
            deduped_list.append(i)

    # sorting isn't super important, but it makes the list easier to read/troubleshoot
    print('Sorting output...')
    sorted_vm_list = sorted(deduped_list, key=lambda x: (x[0], x[2], x[6], x[7]))

    # CSV output can easily be copy/pasted into the ubercalc reference sections
    for vm in sorted_vm_list:
        print( ','.join(vm) )

if __name__ == "__main__":
    get_vm_pricing()
