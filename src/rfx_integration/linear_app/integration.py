import os
import secrets
import requests
from fastapi import HTTPException, FastAPI, Request
from fluvius.fastapi import KCAdmin, config as fastapi_config
from fluvius.data import logger

from . import config

kc_admin = KCAdmin(
    app=None,
    server_url=fastapi_config.KEYCLOAK_BASE_URL,
    client_id=fastapi_config.KEYCLOAK_CLIENT_ID,
    client_secret=fastapi_config.KEYCLOAK_CLIENT_SECRET,
    realm_name=fastapi_config.KEYCLOAK_REALM
)

def get_linear_status_id(status_name):
    """
    Ánh xạ tên trạng thái từ hệ thống của bạn sang ID trạng thái của Linear.
    """
    status_map = {
        "DRAFT": "a291583a-c46a-4096-9df7-ad9046cd39fd",         
        "ACTIVE": "a291583a-c46a-4096-9df7-ad9046cd39fd",      
        "IN_PROGRESS": "022d6dca-d63c-4ee0-9768-40a3c2d99592",
        "PLANNED": "2d517b0e-9395-40ba-a1fa-e1986ee76c7c",      
        "COMPLETED": "3f192138-2d5e-4cc1-97ee-08bd54df6130",   
        "CANCELED": "c4d86fca-29ca-48b1-8a2c-168a7f954d23"     
    }

    return status_map.get(status_name.upper(), None)


def get_linear_user_id(creator_id):
    user_map = {
        "e28bdf52-53fa-412e-87ad-d830f94a7984": "b8g3vffu-ehi5-hdu-e4si-n05uuk-gc7-pnoc"
    }
    return user_map.get(creator_id, None)

def get_linear_label_id(category_name):
    label_map = {
        "ARCHITECTURE": "c78c123d-4c44-5d5e-6a62-78d1ef73c71d"
    }
    return label_map.get(category_name.upper(), None)


def call_linear_api(payload):
    LINEAR_API_URL = config.UAPI_URL
    LINEAR_CONNECTION_ID = config.LINEAR_CONNECTION_ID
    uapi_payload = {
        "connection_id": LINEAR_CONNECTION_ID,
        "action": "call-api",
        "payload": payload
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.request("POST", LINEAR_API_URL, headers=headers, json=uapi_payload)

    return response.json()


def call_linear_api_with_teams(payload, team_ids = None):
    LINEAR_API_URL = config.UAPI_URL
    LINEAR_CONNECTION_ID = config.LINEAR_CONNECTION_ID
    DEFAULT_TEAM_ID = config.DEFAULT_TEAM_ID

    payload["variables"]["input"]["teamIds"] = team_ids or [DEFAULT_TEAM_ID]

    uapi_payload = {
        "connection_id": LINEAR_CONNECTION_ID,
        "action": "call-api",
        "payload": payload
    } 
    
    headers = {
        "Content-Type": "application/json"
    }
        
    response = requests.request("POST", LINEAR_API_URL, headers=headers, json=uapi_payload)
    return response.json()
    
