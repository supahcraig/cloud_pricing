import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request


# these are the instance families we are interested in
instance_families = ['N2', 'N2D AMD']


region_defs = {
    # Americas
    'Iowa': 'us-central1',
    'South Carolina': 'us-east1',
    'Northern Virginia': 'us-east4',
    'Columbus': 'us-east5',
    'Oregon': 'us-west1',
    'Los Angeles': 'us-west2',
    'Salt Lake City': 'us-west3',
    'Las Vegas': 'us-west4',
    'Phoenix': 'us-west8',
    'Dallas': 'us-south1',
    'Montreal': 'northamerica-northeast1',
    'Toronto': 'northamerica-northeast2',
    'Mexico': 'northamerica-south1',
    'Sao Paulo': 'southamerica-east1',
    'Santiago': 'southamerica-west1',
    # Europe
    'Warsaw': 'europe-central2',
    'Belgium': 'europe-west1',
    'London': 'europe-west2',
    'Frankfurt': 'europe-west3',
    'Netherlands': 'europe-west4',
    'Zurich': 'europe-west6',
    'Milan': 'europe-west8',
    'Paris': 'europe-west9',
    'Berlin': 'europe-west10',
    'Turin': 'europe-west12',
    'Finland': 'europe-north1',
    'Stockholm': 'europe-north2',
    'Madrid': 'europe-southwest1',
    # APAC
    'Seoul': 'asia-northeast3',
    'Sydney': 'australia-southeast1',
    'Melbourne': 'australia-southeast2',
    'Taiwan': 'asia-east1',
    'Hong Kong': 'asia-east2',
    'Tokyo': 'asia-northeast1',
    'Osaka': 'asia-northeast2',
    'Mumbai': 'asia-south1',
    'Delhi': 'asia-south2',
    'Singapore': 'asia-southeast1',
    'Jakarta': 'asia-southeast2',
    # Africa
    'Johannesburg': 'africa-south1',
    # Middle East
    'Doha': 'me-central1',
    'Dammam': 'me-central2',
    'Tel Aviv': 'me-west1',
}


def translateCommit(rawCommit):
    # The commit type text must match what is in the dropdown within the Ubercalc
    # That can be set to whatever, but this decoding represents how it shows in the sheet

    commit = ''

    if rawCommit == 'OnDemand':
        commit = 'On Demand'
    elif rawCommit == 'Commit1Yr':
        commit = '1 Year Commit'
    elif rawCommit == 'Commit3Yr':
        commit = '3 Year Commit'

    return commit

def lookupMissingRegion(region, fullDescription):
    # The region code may not be in the region_defs lookup
    # if you run into one that isn't it's best to add it manually to the region_defs dict
    # and that's why we raise missing ones as an exception

    try:
        region_name = list(region_defs.keys())[list(region_defs.values()).index(region)]

        return region_name

    except ValueError:
        print(f'Region missing from region_defs dict:  {region}: full description= ', fullDescription)

        # TODO actually add the region code/name to a lookup.
        raise


def get_vm_pricing():
    # Path to your service account key file
    key_file_path = "./ubercalc_creds.json"

    # Create credentials using the service account key
    scopes = ["https://www.googleapis.com/auth/cloud-billing"]
    credentials = service_account.Credentials.from_service_account_file(key_file_path, scopes=scopes)

    # Refresh the token to ensure it's valid
    credentials.refresh(Request())
    access_token = credentials.token

    # Service ID for Compute Engine
    service_id = "6F81-5844-456A"  # Service ID for Compute Engine
    pricing_url = f"https://cloudbilling.googleapis.com/v1/services/{service_id}/skus"


    vm_attribs = []

    page_token = None

    while True:

        params = {}
        if page_token:
            params['pageToken'] = page_token

        # Make a GET request to the pricing API
        response = requests.get(pricing_url, headers={"Authorization": f"Bearer {access_token}"}, params=params)

        if response.status_code == 200:
            pricing_info = response.json()

            for sku in pricing_info.get("skus", []):
                #print(sku)

                for instance_family in instance_families:

                    if (f'{instance_family} Instance Core' in sku['description'] or
                            f'Commitment v1: {instance_family} Cpu' in sku['description'] or
                            f'{instance_family} Instance Ram' in sku['description'] or
                            f'Commitment v1: {instance_family} Ram' in sku['description'] or
                            'SSD backed Local Storage' in sku['description'] or
                            'Commitment v1: Local SSD' in sku['description']
                             ) and \
                            'Preemptible' not in sku['description']:

                        commit = translateCommit(sku['category']['usageType'])

                        modified_family = ''
                        if 'SSD' in sku['description']:
                            modified_family = '<local ssd>'
                        else:
                            modified_family = instance_family.replace('AMD', '').strip()  # instance type, this might end up being fragile

                        # some cases have multiple regions attached to a single SKU, so this explodes that to a line per region
                        for region in sku['serviceRegions']:
                            region_name = lookupMissingRegion(region, sku['description'])

                            attrib = [region,
                                      region_name,
                                      modified_family,
                                      '', # placeholder--required
                                      '', # placeholder--required
                                      str(sku['pricingInfo'][0]['pricingExpression']['tieredRates'][0]['unitPrice']['nanos'] / 1000000000),
                                      sku['category']['resourceGroup'],
                                      commit,
                                    ]

                            vm_attribs.append(attrib)

                    # troubleshooting block
                    elif 'N2 ' in sku['description']:
                        pass
                        #print(sku)

                    # troubleshooting block
                    elif sku['serviceRegions'][0] == 'me-central1':
                        pass
                        #print(sku)

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
