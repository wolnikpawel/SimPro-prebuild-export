import requests
import pandas as pd
import os
import logging
from datetime import datetime

BASE_URL = os.environ.get("BASE_URL")
FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
DATE_STAMP = datetime.now().strftime("%Y-%m-%d")
OUTPUT_FILE = os.path.join(FOLDER_PATH, f"prebuild_{DATE_STAMP}.xlsx")
LOG_FILE = os.path.join(FOLDER_PATH, "prebuild_log.txt")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s', filemode='w')
logging.getLogger().addHandler(logging.StreamHandler())


def get_prebuilds_by_type(token, company_id, prebuild_type):
    url = f"{BASE_URL}/companies/{company_id}/prebuilds/{prebuild_type}/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        logging.info(f"✅ Fetched {prebuild_type} prebuilds list.")
        return response.json()
    else:
        logging.error(f"❌ Failed to get {prebuild_type} list: {response.status_code} - {response.text}")
        return []


def get_prebuild_detail(token, company_id, prebuild_id, prebuild_type):
    url = f"{BASE_URL}/companies/{company_id}/prebuilds/{prebuild_type}/{prebuild_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.warning(f"⚠️ Failed to fetch prebuild {prebuild_id} ({prebuild_type}): {response.status_code}")
        return None


def get_catalog_items(token, company_id, prebuild_id):
    url = f"{BASE_URL}/companies/{company_id}/prebuilds/{prebuild_id}/catalogs/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.warning(f"⚠️ Failed to fetch catalog items for prebuild {prebuild_id}: {response.status_code}")
        return []


def flatten_prebuild(prebuild):
    flat = prebuild.copy()

    if isinstance(prebuild.get('Group'), dict):
        for k, v in prebuild['Group'].items():
            flat[f"Group_{k}"] = v
        flat.pop('Group', None)

    if isinstance(prebuild.get('SalesTaxCode'), dict):
        for k, v in prebuild['SalesTaxCode'].items():
            flat[f"SalesTaxCode_{k}"] = v
        flat.pop('SalesTaxCode', None)

    return flat


def flatten_catalog_item(item):
    flat = {}
    for key, value in item.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat[f"{key}_{sub_key}"] = sub_value
        else:
            flat[key] = value
    return flat


def sanitize_excel_formulas(df):
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: f"'{x}" if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x
        )
    return df


def extract_prebuilds(token, company_id):
    if not token:
        logging.error("❌ No token provided.")
        return pd.DataFrame()

    detailed_rows = []

    for prebuild_type in ["standardPrice", "setPrice"]:
        summary_list = get_prebuilds_by_type(token, company_id, prebuild_type)
        logging.info(f"🔄 Found {len(summary_list)} {prebuild_type} prebuilds")

        for item in summary_list:
            prebuild_id = item.get("ID")
            if not prebuild_id:
                continue

            logging.info(f"🔍 Getting {prebuild_type} prebuild ID: {prebuild_id}")
            details = get_prebuild_detail(token, company_id, prebuild_id, prebuild_type)
            if not details:
                continue

            base_data = flatten_prebuild(details)
            base_data['PrebuildSource'] = prebuild_type

            catalog_items = get_catalog_items(token, company_id, prebuild_id)
            if not catalog_items:
                detailed_rows.append(base_data)
                continue

            for component in catalog_items:
                component_data = flatten_catalog_item(component)
                combined_row = {**base_data, **component_data}
                detailed_rows.append(combined_row)

    if detailed_rows:
        df = pd.DataFrame(detailed_rows)
        df = sanitize_excel_formulas(df)
        logging.info(f"✅ Extracted {len(df)} rows of prebuild data.")
        return df
    else:
        logging.warning("⚠️ No prebuild data found.")
        return pd.DataFrame()