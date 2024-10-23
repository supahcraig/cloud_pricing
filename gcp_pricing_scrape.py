import requests
from bs4 import BeautifulSoup

# First and foremost, the GCP pricing API is literally the worst thing ever.
# In order to get pricing for a compute type, you must first know the SKU for the instance type, region, and commit.

# Those SKUs are found on a handful of pages (all skus found here: https://cloud.google.com/skus/sku-groups)
# There is a single SKU for each combination of instance type, region, commit, and also one for CPU & one for  Memory.

# To further complicate things the API doesn't return these details so you have to parse them from the web page itself.

# And because who doesn't love a challenge, the regions listed on the page don't always correspond to the regions you
# are probably familiar with.  Case in point, "Americas" is a region attached to a SKU but it contains 3 actual regions.
# The only way to know what those regions are is to navigate to that specific SKU and observe what the actual regions
# are.   That is why the dictionary "api_region_groups" exists.   NOTE that this will almost certainly change over time
# and will require further updates to this region mapping.


#call = f"{url}beta/skus/{vm_sku}/price?key={api_key}"

call_count = 0

api_key = '' # your API key goes here, keep it secure.
url = "https://cloudbilling.googleapis.com/v1"



sku_group_pages_vms = [{'compute type': 'N2', 'commit': '1 Year Commit', 'link suffix': 'n2-vms-1-year-cud'},
                       {'compute type': 'N2', 'commit': '3 Year Commit', 'link suffix': 'n2-vms-3-year-cud'},
                       {'compute type': 'N2D', 'commit': '1 Year Commit', 'link suffix': 'n2d-vms-1-year-cud'},
                       {'compute type': 'N2D', 'commit': '3 Year Commit', 'link suffix': 'n2d-vms-3-year-cud'},
                       {'compute type': 'N2', 'commit': 'On Demand', 'link suffix': 'on-demand-n2-vms'},
                       {'compute type': 'N2D', 'commit': 'On Demand', 'link suffix': 'on-demand-n2d-vms'},
                       ]

sku_group_pages_ssds = [{'commit': '1 Year Commit', 'link suffix': 'local-ssds-1-year-cud'},
                       {'commit': '3 Year Commit', 'link suffix': 'local-ssds-3-year-cud'},
                       {'commit': 'On Demand', 'link suffix': 'on-demand-local-ssd'},
                       ]



api_region_groups = {
    'APAC': ['asia-east1'],
    'Americas': ['us-central1', 'us-east1', 'us-west1'],
    'EMEA': ['europe-west1'],
    'Japan': ['asia-northeast1'],
    'Israel': ['me-west1'],
    'Virginia': ['us-east4']
    ,'SSD-Various': ['us-central1', 'us-east1', 'us-west1', 'asia-east1', 'europe-west1']
}

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
    'Dallas': 'us-south1',
    'Montreal': 'northamerica-northeast1',
    'Toronto': 'northamerica-northeast2',
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
    'Jakarta': 'asia-southseat2',
    # Africa
    'Johannesburg': 'africa-south1',
    # Middle East
    'Dammam': 'me-central2',
    'Tel Aviv': 'me-west1',
}

def region_lookup(r):
    try:
        name = region_defs[r]
        yield name

    except KeyError:
        try:
            for name in api_region_groups[r]:
                yield name
        except KeyError:
            print(f'Region {r} is not in the region_def lookup')
            yield(f'Region {r} is not in the region_def lookup')


def fetch_sku_group_page(sku_group):
    # Each list of relevant skus is on a separate page based on compute type & commit
    # so we have to iterate over each of those pages

    HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    URL = f'https://cloud.google.com/skus/sku-groups/{sku_group}'

    page = requests.get(URL, headers=HEADERS)

    #print(page)

    soup = BeautifulSoup(page.content, 'html.parser')
    # print(soup)

    return soup


def get_sku_list(soup):
    # within each page is a list of skus for the different regions
    # we need each of those skus & their region to call the API to get the pricing

    # this is the div where thos SKUs & descriptions are held
    div_container = soup.find("div", class_="devsite-article-body clearfix")

    sku_list = []
    for sku in div_container.find_all('tr'):
        i = 0
        sku_dict = {}

        for field in sku.find_all("td"):
            i += 1

            # this is a little too fragile but I'm not sure how to do it in a more pythonic way
            # we have to parse the region & commitment from the text in the page for that sku.  Thanks GCP.
            match i:
                case 1:
                    # sku_dict['compute engine'] = field.text
                    pass

                case 2:
                    #print(field.text)
                    if ' Cpu in ' in field.text:
                        L1 = field.text.partition("Cpu in ")
                        L2 = L1[2].partition(" for")
                        sku_dict['region'] = L2[0]
                        sku_dict['resource type'] = 'CPU'

                    elif ' Instance Core ' in field.text \
                            and ' Custom ' not in field.text \
                            and ' Sole Tenancy ' not in field.text:
                        # not Custom Instance Core
                        # not Custom Extended Instance Ram
                        # not Custom Instance Ram
                        # YES Instance Core
                        # YES Instance Ram
                        # not Sole Tenancy Instance Core
                        # not Sole Tenancy Instance Ram
                        L1 = field.text.partition("Core running in ")
                        #L2 = L1[2].partition(" for")
                        sku_dict['region'] = L1[2]
                        sku_dict['resource type'] = 'CPU'

                    elif ' Instance Ram ' in field.text \
                            and ' Custom ' not in field.text \
                            and ' Sole Tenancy ' not in field.text:
                        # not Custom Instance Core
                        # not Custom Extended Instance Ram
                        # not Custom Instance Ram
                        # YES Instance Core
                        # YES Instance Ram
                        # not Sole Tenancy Instance Core
                        # not Sole Tenancy Instance Ram
                        L1 = field.text.partition("Ram running in ")
                        sku_dict['region'] = L1[2]
                        sku_dict['resource type'] = 'Memory'

                    elif ' Ram in ' in field.text:
                        L1 = field.text.partition("Ram in ")
                        L2 = L1[2].partition(" for")
                        sku_dict['region'] = L2[0]
                        sku_dict['resource type'] = 'Memory'

                    elif ' Local SSD in ' in field.text:
                        L1 = field.text.partition(" Local SSD in ")
                        L2 = L1[2].partition(" for ")
                        sku_dict['region'] = L2[0]
                        sku_dict['resource type'] = 'SSD'

                    elif 'SSD backed Local Storage in' in field.text\
                            and ' Spot ' not in field.text:
                        L1 = field.text.partition("SSD backed Local Storage in ")
                        sku_dict['region'] = L1[2]
                        sku_dict['resource type'] = 'SSD'

                    elif field.text == 'SSD backed Local Storage':
                        # this is such a horrible thing to have to code, but the Google API was created by idiots
                        # this is a fabricated region will will have a custom mapping herein
                        # but there is no way to programmatically know if this mapping evolves over time
                        sku_dict['region'] = 'SSD-Various'
                        sku_dict['resource type'] = 'SSD'


                case 3:
                    sku_dict['sku'] = field.text

        if sku_dict != {}:
            sku_list.append(sku_dict)

    return sku_list


def get_raw_price_list(sku_list, compute_type, commit, api_key):
    # Call the pricing API for each sku
    # note that the region is being parsed from web page text...
    # ...and some "regions" are actually groups of regions (e.g. "Americas")

    global call_count

    raw_price_list = []
    for sku in sku_list:
        p = {}

        call = f"{url}beta/skus/{sku['sku']}/price?key={api_key}"

        r = requests.get(call)
        call_count += 1
        response = r.json()

        try:
            rate_nanos = response['rate']['tiers'][0]['listPrice']['nanos']
        except KeyError:
            print(response)
            raise

        try:
            p['region'] = sku['region']
            p['compute_type'] = compute_type
            p['resource type'] = sku['resource type']
            p['commit'] = commit
            p['hourly_rate'] = rate_nanos / 1000000000
            p['sku'] = sku['sku']
            # print(p)
            raw_price_list.append(p)
        except KeyError:
            # the keys are missing if the sku is one we're going to ignore
            # this use case comes up during the SSD pricing
            pass

    return raw_price_list


def format_output(raw_price_list):
    sorted_price_list = sorted(raw_price_list, key=lambda x: (x['region'],
                                                              x['compute_type'],
                                                              x['resource type'],
                                                              x['commit']))

    for sku in sorted_price_list:
        for r in region_lookup(sku['region']):
            if 'is not in the region_def lookup' not in r:

                # The placeholder fields are necessary because if we ever need to manually copy/pasta this data
                # from the pricing webpage into the Ubercalc, there are additional fields.
                attrib = [r,
                          sku['region'],
                          sku['compute_type'],
                          '',  # placeholder fields are necessary
                          '',  # placeholder fields are necessary
                          str(sku['hourly_rate']),
                          sku['resource type'],
                          sku['commit']]

                csv = ','.join(attrib)
                print(csv)





def vm_price_list():
    raw_price_list = []
    for page in sku_group_pages_vms:
        print(page)

        soup = fetch_sku_group_page(sku_group=page['link suffix'])

        try:
            compute_type = page['compute type']
        except KeyError:
            compute_type = ''

        commit = page['commit']

        sku_list = get_sku_list(soup)

        raw_price_list.extend(get_raw_price_list(sku_list, compute_type, commit, api_key))

    format_output(raw_price_list)


def ssd_price_list():
    raw_price_list = []
    for page in sku_group_pages_ssds:

        soup = fetch_sku_group_page(sku_group=page['link suffix'])

        try:
            compute_type = page['compute type']
        except KeyError:
            compute_type = ''

        commit = page['commit']

        sku_list = get_sku_list(soup)

        raw_price_list.extend(get_raw_price_list(sku_list, compute_type, commit, api_key))

    format_output(raw_price_list)


def build_price_list(resource_type):
    raw_price_list = []

    if resource_type == 'ssd':
        sku_page = sku_group_pages_ssds
    elif resource_type == 'vm':
        sku_page = sku_group_pages_vms
    else:
        exit(99)

    for page in sku_page:

        soup = fetch_sku_group_page(sku_group=page['link suffix'])

        try:
            compute_type = page['compute type']
        except KeyError:
            compute_type = ''

        commit = page['commit']

        sku_list = get_sku_list(soup)

        raw_price_list.extend(get_raw_price_list(sku_list, compute_type, commit, api_key))

    format_output(raw_price_list)



#build_price_list('ssd')

#ssd_price_list()
vm_price_list()
print(f'Total number of calls to API = {call_count}')

