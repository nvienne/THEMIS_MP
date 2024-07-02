from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import os
import csv
import pandas as pd
import base64




def save_to_csv(filenames, urls, csv_name):
    if not os.path.exists(csv_name):  # Check if file exists
        with open(csv_name, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Filename', 'URL'])  # Write header
    data = pd.DataFrame({
        'Filename': filenames,
        'URL': urls
    })
    data.to_csv(csv_name, mode='a', header=False, index=False)

def scrape_ATF(base_url, csv_name, total_pages):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(executable_path=r"E:\THEMIS\4. Admin\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(base_url)
    time.sleep(7)  # Wait for the page to load

    pbar = tqdm(total=total_pages, desc="Scraping pages", unit="page")
    current_page = 0  # Initialize page counter

    while current_page < total_pages:
        wait = WebDriverWait(driver, 25)
        law_links_xpath = "/html/body/div[1]/div[3]/div[3]/div/main/div[1]/div[5]/div[2]/div/div[3]/div[2]/ol/li/span/a"
        try:
            law_links = wait.until(EC.presence_of_all_elements_located((By.XPATH, law_links_xpath)))
            current_filenames = [link.text.replace("/", "-") for link in law_links]
            current_urls = [link.get_attribute('href') for link in law_links]
            save_to_csv(current_filenames, current_urls, csv_name)

        except TimeoutException:
            print(f"No links found on {driver.current_url}. Attempting to move to the next page.")

        current_page += 1  # Increment page counter after processing each page
        pbar.update(1)

        if current_page >= total_pages:
            print("Reached the specified number of pages to scrape.")
            break

        try:
            next_button_xpath = "/html/body/div[1]/div[3]/div[3]/div/main/div[1]/div[5]/div[2]/div/div[3]/div[3]/div/a[last()]"
            next_button = wait.until(EC.presence_of_element_located((By.XPATH, next_button_xpath)))

            if next_button.text.lower() != "suivante":  # Check if "next" button text is as expected
                print("May have reached the last page earlier than expected.")
                break

            next_button.click()
            time.sleep(5)  # Wait for the next page to load

        except (NoSuchElementException, IndexError):
            print("Failed to find the 'next' button or reached the end of the pages.")
            break

    pbar.close()
    print("Completed scraping.")
    driver.quit()

def setup_driver(download_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(executable_path=r"E:\THEMIS\4. Admin\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def process_url(url, download_path, filename):
    driver = setup_driver(download_path)
    try:
        time.sleep(1)
        driver.get(url)
        # WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        time.sleep(4)

        # Use provided filename for the PDF
        full_filename = f"{filename}.pdf"

        # Updated part: Print page to PDF using the updated CDP command
        print_to_pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False,
            "printBackground": True,
            "preferCSSPageSize": True,
        })
        pdf_content = base64.b64decode(print_to_pdf['data'])
        full_path = os.path.join(download_path, full_filename)
        with open(full_path, 'wb') as f:
            f.write(pdf_content)
        time.sleep(2)  # Small buffer to ensure the PDF is saved

        # Print the path to the terminal
        print(f"PDF saved: {full_path}")
        
        return full_path
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None
    finally:
        driver.quit()

def collect_pdf_general(csv_path, download_path, problematic_urls_path, start_row, threads=6):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Extract URLs and filenames starting from a specified row
    urls = df['URL'][start_row:].tolist()
    filenames = df['Filename'][start_row:].tolist()

    # Dictionary to hold the mapping of URLs to downloaded filenames
    downloaded_files = {}

    # List to hold URLs that had problems during download
    problematic_urls = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        progress = tqdm(total=len(urls), desc="Processing URLs")
        future_to_url = {}

        for url, filename in zip(urls, filenames):
            future = executor.submit(process_url, url, download_path, filename)
            future_to_url[future] = url
            progress.update(1)

        for future in tqdm(as_completed(future_to_url), total=len(urls), desc="Processing URLs"):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    # If download is successful, save the downloaded filename
                    downloaded_files[url] = result
                else:
                    problematic_urls.append(url)
            except Exception as e:
                problematic_urls.append(url)
                print(f"URL {url} generated an exception: {e}")

    # Update the DataFrame with the downloaded filenames
    for url, downloaded_file in downloaded_files.items():
        df.loc[df['URL'] == url, 'Filename_pdf'] = downloaded_file.split('\\')[-1]

    # Save the updated DataFrame
    df.to_csv(csv_path, index=False)

    # Log problematic URLs, if any
    if problematic_urls:
        pd.DataFrame(problematic_urls, columns=['Problematic URLs']).to_csv(problematic_urls_path, mode='a', header=not os.path.exists(problematic_urls_path), index=False)

    print(f"Problematic URLs are logged in: {problematic_urls_path}")

def merge_csv_files(directory_path, output_file):
    # List to hold the data from each CSV
    merged_data = []

    # Walk through the directory to find CSV files
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                # Read the CSV file
                data = pd.read_csv(file_path)
                # Check if the CSV has exactly 'Filename' and 'URL' columns
                if sorted(data.columns) == ['Filename', 'URL']:
                    merged_data.append(data)
                else:
                    print(f"Skipped {file_path} due to incorrect columns.")

    # Concatenate all dataframes in the list
    if merged_data:
        final_df = pd.concat(merged_data, ignore_index=True)
        # Save the merged data to a new CSV file
        final_df.to_csv(output_file, index=False)
        print(f"Merged data has been saved to {output_file}.")
    else:
        print("No valid CSV files found to merge.")


# merge_csv_files(r"E:\ASSURANCES\1. Documents\ATF", r"E:\ASSURANCES\3. Data base\DB_Assurances.csv")
# merge_csv_files(r"E:\SOCIAL\1. Documents\ATF", r"E:\SOCIAL\3. Data base\DB_Social.csv")
# merge_csv_files(r"E:\TRAVAIL\1. Documents\ATF", r"E:\TRAVAIL\3. Data base\DB_Travail.csv")
# merge_csv_files(r"E:\ASILE\1. Documents\ATF", r"E:\ASILE\3. Data base\DB_Asile.csv")
# merge_csv_files(r"E:\IMPOTS\1. Documents\ATF", r"E:\IMPOTS\3. Data base\DB_Impôts.csv")


# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=asile&lang=fr&top_subcollection_aza=all&from_date=01.01.2000&to_date=29.04.2024"
# scrape_ATF(ATF, r"E:\ASILE\1. Documents\ATF\metadata_ATF.csv", 156)




# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2019&to_date=31.12.2021&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_2.csv", 172)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2016&to_date=31.12.2018&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_3.csv", 178)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2013&to_date=31.12.2015&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_4.csv", 176)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2010&to_date=31.12.2012&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_5.csv", 200)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2008&to_date=31.12.2009&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_6.csv", 143)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=social&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2000&to_date=31.12.2007&x=0&y=0"
# scrape_ATF(ATF, r"E:\SOCIAL\1. Documents\ATF\metadata_ATF_7.csv", 170)




# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2022&to_date=28%2F04%2F2024&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_1.csv", 162)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2020&to_date=31.12.2021&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_2.csv", 145)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2018&to_date=31.12.2019&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_3.csv", 150)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2015&to_date=31.12.2017&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_4.csv", 200)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2012&to_date=31.12.2014&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_5.csv", 197)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2010&to_date=31.12.2011&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_6.csv", 136)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2008&to_date=31.12.2009&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_7.csv", 149)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2006&to_date=31.12.2007&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_8.csv", 158)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2003&to_date=31.12.2005&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_9.csv", 189)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=travail&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2000&to_date=31.12.2002&x=0&y=0"
# scrape_ATF(ATF, r"E:\TRAVAIL\1. Documents\ATF\metadata_ATF_10.csv", 145)




# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=impot&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2012&to_date=28%2F04%2F2024&x=0&y=0"
# scrape_ATF(ATF, r"E:\IMPOTS\1. Documents\ATF\metadata_ATF_1.csv", 199)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=impot&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2000&to_date=31.12.2011&x=0&y=0"
# scrape_ATF(ATF, r"E:\IMPOTS\1. Documents\ATF\metadata_ATF_2.csv", 102)




# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2021&to_date=28%2F04%2F2024&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_1.csv", 189)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2018&to_date=31.12.2020&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_2.csv", 175)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2015&to_date=31.12.2017&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_3.csv", 169)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2012&to_date=31.12.2014&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_4.csv", 184)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2010&to_date=31.12.2011&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_5.csv", 136)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2008&to_date=31.12.2009&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_6.csv", 154)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2006&to_date=31.12.2007&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_7.csv", 163)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2005&to_date=31.12.2006&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_8.csv", 148)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2002&to_date=31.12.2004&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_9.csv", 174)

# ATF = "https://www.bger.ch/ext/eurospider/live/fr/php/aza/http/index.php?lang=fr&type=simple_query&query_words=assurance&lang=fr&top_subcollection_aza=all&from_date=01%2F01%2F2000&to_date=31.12.2001&x=0&y=0"
# scrape_ATF(ATF, r"E:\ASSURANCES\1. Documents\ATF\metadata_ATF_10.csv", 110)



# collect_pdf_general(csv_path=r"E:\SOCIAL\3. Data base\DB_Social.csv", download_path=r"E:\SOCIAL\1. Documents\ATF", problematic_urls_path=r"E:\SOCIAL\1. Documents\ATF\problematic.csv", start_row=7000, threads=4)
# collect_pdf_general(csv_path=r"E:\TRAVAIL\3. Data base\DB_Travail.csv", download_path=r"E:\TRAVAIL\1. Documents\ATF", problematic_urls_path=r"E:\TRAVAIL\1. Documents\ATF\problematic.csv", start_row=0, threads=5)
# collect_pdf_general(csv_path=r"E:\IMPOTS\3. Data base\DB_Impôts.csv", download_path=r"E:\IMPOTS\1. Documents\ATF", problematic_urls_path=r"E:\IMPOTS\1. Documents\ATF\problematic.csv", start_row=0, threads=5)
# collect_pdf_general(csv_path=r"E:\ASSURANCES\3. Data base\DB_Assurances.csv", download_path=r"E:\ASSURANCES\1. Documents\ATF", problematic_urls_path=r"E:\ASSURANCES\1. Documents\ATF\problematic.csv", start_row=0, threads=4)
# collect_pdf_general(csv_path=r"E:\ASILE\3. Data base\DB_Asile.csv", download_path=r"E:\ASILE\1. Documents\ATF", problematic_urls_path=r"E:\ASSURANCES\1. Documents\ATF\problematic.csv", start_row=0, threads=4)


