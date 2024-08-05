import requests



################## UTIL

def get_list_of_cantons(base_url="https://www.simap.ch"):
    endpoint = "/api/cantons/v1"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        # Check if the response content type is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()  # Assuming the response is in JSON format
            # Debug output to see the JSON structure
            print(f"Response JSON: {data}")
            
            # Extract the list of cantons
            cantons = data.get("cantons", [])
            return cantons
        else:
            print(f"Unexpected content type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None



################## CODES

def get_list_of_cpv_codes(base_url="https://www.simap.ch", parent_code=""):

    endpoint = "/api/codes/v1/cpv"
    url = f"{base_url}{endpoint}"
    params = {"parentCode": parent_code}
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"}, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        # Check if the response content type is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()  # Assuming the response is in JSON format
            # Debug output to see the JSON structure
            print(f"Response JSON: {data}")
            
            # Extract the list of CPV codes
            cpv_codes = data.get("codes", [])
            return cpv_codes
        else:
            print(f"Unexpected content type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_list_of_cpc_codes(base_url="https://www.simap.ch"):
    """
    Fetch the list of CPC codes from the API endpoint.

    Args:
    base_url (str): The base URL of the API.

    Returns:
    list: A list of CPC codes if the request is successful, otherwise None.
    """
    endpoint = "/api/codes/v1/cpc"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        # Check if the response content type is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()  # Assuming the response is in JSON format
            # Debug output to see the JSON structure
            print(f"Response JSON: {data}")
            
            # Extract the list of CPC codes
            cpc_codes = data.get("codes", [])
            return cpc_codes
        else:
            print(f"Unexpected content type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def print_cpc_codes(cpc_codes):
    if cpc_codes:
        print("List of CPC codes:")
        for code in cpc_codes:
            print(f"ID: {code['id']}")
            print("Labels:")
            for lang, label in code['label'].items():
                print(f"  {lang.upper()}: {label}")
            print("-" * 40)
    else:
        print("Failed to retrieve the list of CPC codes or the list is empty.")



################## INSTITUTIONS
        
def get_list_of_institutions(base_url="https://www.simap.ch"):
    """
    Fetch the list of institutions from the API endpoint.

    Args:
    base_url (str): The base URL of the API.

    Returns:
    list: A list of institutions if the request is successful, otherwise None.
    """
    endpoint = "/api/institutions/v1"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        # Check if the response content type is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()  # Assuming the response is in JSON format
            # Debug output to see the JSON structure
            print(f"Response JSON: {data}")
            
            # Extract the list of institutions
            institutions = data.get("institutions", [])
            return institutions
        else:
            print(f"Unexpected content type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def print_institutions(institutions):
    if institutions:
        print("List of institutions:")
        for institution in institutions:
            print(f"ID: {institution['id']}")
            print("Names:")
            for lang, name in institution['name'].items():
                print(f"  {lang.upper()}: {name}")
            print(f"Handles Procurement Office Types: {', '.join(institution['handlesProcOfficesTypes'])}")
            print(f"User Can Create Procurement Office: {institution['userCanCreateProcOffice']}")
            print(f"Has Institutions: {institution['hasInstitutions']}")
            print(f"Has Procurement Offices: {institution['hasProcOffices']}")
            print(f"Competence Centre ID: {institution['compCentreId']}")
            print("-" * 40)
    else:
        print("Failed to retrieve the list of institutions or the list is empty.")

def get_list_of_institutions_query(query, base_url="https://www.simap.ch"):
    """
    Fetch the list of procurement offices from the API endpoint based on the provided query.

    Args:
    query (str): The search query to find procurement offices.
    base_url (str): The base URL of the API.

    Returns:
    list: A list of procurement offices if the request is successful, otherwise None.
    """
    if len(query) < 3:
        print("Query must be at least 3 characters long.")
        return None

    endpoint = "/api/institutions/v1/po/search"
    url = f"{base_url}{endpoint}"
    params = {"query": query}
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"}, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        # Check if the response content type is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()  # Assuming the response is in JSON format
            # Debug output to see the JSON structure
            print(f"Response JSON: {data}")
            
            # Extract the list of institutions
            institutions = data.get("institutions", [])
            return institutions
        else:
            print(f"Unexpected content type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
institutions = get_list_of_institutions_query("Gemeinde Bern")
print(institutions)
