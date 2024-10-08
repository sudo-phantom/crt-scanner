import requests
import argparse
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from utilities import HeaderCheck
import selenium
import urllib3
import sys
import json
import os


# open google chrome with selenium

options = Options()
options.add_argument("--headless")
options.add_argument("--incognito")
driver = webdriver.Chrome(options=options)
BASE_URL = "https://crt.sh/?q={}&output=json&opt=excludeExpired"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}

parser = argparse.ArgumentParser(
    epilog="\tExample: \r\npython3 " + sys.argv[0] + " -d google.com"
)
parser._optionals.title = "OPTIONS"
parser.add_argument(
    "-d",
    "--domain",
    type=str,
    help="Specify Target Domain to get subdomains from crt.sh",
    required=True,
)
query = parser.parse_args()
dname = query.domain
cname = "common_name"


class FileHandle:
    """class for the file handling of the script."""

    def __init__(self, fname, data) -> None:
        self.fname = fname
        self.data = data

    def write_file(fname, data):
        """write to file."""
        subfolder = f"{dname}/{fname}"
        if not os.path.exists(dname):
            os.mkdir(dname)
        if not os.path.exists(subfolder):
            os.mkdir(subfolder)
        with open(f"{subfolder}/{fname}", "w", encoding="utf-8") as file:
            file.write(data)
            file.close()


def get_data():
    """get json output from crt.sh and output to file named [domain]-output.json"""
    url_list = []
    url = BASE_URL.format(str(dname))
    r = requests.get(url, headers=headers, timeout=25)
    response = r.json()
    output = json.dumps(response)
    print("---------------------------\n")
    print(f" + Discovering domains for {dname} \n")
    FileHandle.write_file(fname=f"crt-results-for-{dname}.json", data=output)
    for each in response:
        domain_name = each["common_name"]

        if domain_name not in url_list:
            print(f"+ common name found: {domain_name}")
            if "*" not in domain_name:
                url_list.append(domain_name)
    return url_list


def check_url():
    """function to check if urls respond, and if so get the data"""
    domain_list = get_data()
    count = 0

    for d in domain_list:
        count += 1
        url = "https://" + d
        subdir = f"{dname}/{d}"
        header_data = HeaderCheck.get_headers.scan_it([url])
        resp = ""
        try:
            r = requests.get(url, headers=headers, timeout=25)
            sleep(0.5)
            resp = r.status_code
        except requests.exceptions.ConnectionError:
            pass
        if str(20) in str(resp) or str(30) in str(resp):
            call_data = r.text
            print(f"+ Domain discovered: {d} \n")
            FileHandle.write_file(d, call_data)

            try:
                driver.get(url)
                sleep(3)
                print(f"+ capturing screenshot of {d}")
                driver.save_screenshot(f"{subdir}/{d}.png")
                with open(
                    f"{subdir}/{d}-header-data.txt", "w", encoding="utf-8"
                ) as file:
                    file.write(str(header_data))
                    file.close()
                sleep(1)
            except (
                ConnectionError,
                ConnectionRefusedError,
                urllib3.exceptions.MaxRetryError,
            ) as e:
                driver.quit()
                sleep(1)
                print(f"failed to capture {url}")
                with open(f"{dname}/errorlog.log", "w", encoding="utf-8") as f:
                    f.write(str(e))
            finally:
                
                r.close()
        else:
            FileHandle.write_file(d, str(resp))
            print("- Domain not accepting http requests.")
    print(f"+ Found [{count}]: urls, available at /{dname}")


check_url()
