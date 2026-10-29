import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EMPTY_CLP_VALUES = ['Please select a static block.', '']
DEFAULT_CLP_LABEL = 'Use Default Value'
DEFAULT_CLP_STOREVIEW = 'Default Store View'

DIVISIONS = ["div1", "div2", "div3", "div4", "div5", "div6", "div7", "div8", "div9", "div10"]

# Shared Magento username with a per-division password, e.g. MAGENTO_PASSWORD_DIV1
MAGENTO_USERNAME = os.getenv("MAGENTO_USERNAME", "")
MAGENTO_CREDENTIALS = {
    division: {
        "username": MAGENTO_USERNAME,
        "password": os.getenv(f"MAGENTO_PASSWORD_{division.upper()}", ""),
    }
    for division in DIVISIONS
}

# Base admin URLs (without the trailing "dashboard" route) used to build other admin URLs
DIVISIONS_URL = {
    "div1": "https://div1.shopdutyfree.com/adminpanel/",
    "div2": "https://div2.shopdutyfree.com/adminpanel/",
    "div3": "https://div3.shopdutyfree.com/adminpanel/",
    "div4": "https://div4.shopdutyfree.com/adminpanel/",
    "div5": "https://div5.shopdutyfree.com/adminpanel/",
    "div6": "https://div6.shopdutyfree.com/admin_pah4i6/",
    "div7": "https://div7.shopdutyfree.com/admin_x1w3p0/",
    "div8": "https://div8.shopdutyfree.com/adminpanel/",
    "div9": "https://div9.shopdutyfree.com/adminpanel/",
    "div10": "https://div10.shopdutyfree.com/admin_x1w3p0/",
}   

DIVISIONS_CLP = {
    "div1": "https://div1.shopdutyfree.com/adminpanel/catalog/category/edit/id/{category_id}/store/{store_id}/",
    "div2": "https://div2.shopdutyfree.com/adminpanel/catalog/category/edit/id/{category_id}/store/{store_id}/",
    "div3": "https://div3.shopdutyfree.com/adminpanel/catalog/category/edit/id/{category_id}/store/{store_id}/",
    "div4": "https://div4.shopdutyfree.com/adminpanel/catalog/category/edit/id/{category_id}/store/{store_id}/",
    "div5": "https://div5.shopdutyfree.com/adminpanel/catalog/category/edit/id/{category_id}/store/{store_id}/",
    "div6": "https://div6.shopdutyfree.com/admin_pah4i6/catalog/category/edit/id/{category_id}/store/{store_id}/"
}

MAGENTO_BRANDS_URL = "brandboutique/brand/index/"
MAGENTO_CATEGORIES_URL = "brandboutique/category/index/"
MAGENTO_COLLECTIONS_URL = "brandboutique/range/index/"

# CLUB AVOLTA APP
APP_STAGING_URL = "https://stage-club-avolta.euwest01.umbraco.io/umbraco#/content"
APP_STAGING_HOMEID = 6583
APP_PROD_URL = "https://club-avolta.euwest01.umbraco.io/umbraco#/content"
APP_PROD_HOMEID = 5677

APP_CREDENTIALS = {
    "username": os.getenv("APP_USERNAME", ""),
    "password": os.getenv("APP_PASSWORD", ""),
}

APP_DEFAULT_LANGUAGE = "en-US"
APP_LANGUAGES = ['ar', 'zh', 'zh-HK', 'zh-CN', 'da', 'fi-FI', 'fr', 'de', 'el', 'id', 'it-IT', 'ko', 'ms', 'no', 'pt-BR', 'ru', 'es', 'sv-SE', 'th-TH', 'tr-TR', 'vi']
