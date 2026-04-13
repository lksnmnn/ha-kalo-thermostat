"""Constants for the KALO Thermostat integration."""

DOMAIN = "kalo_thermostat"

PLATFORMS = ["binary_sensor", "climate", "sensor", "switch"]

# Beyonnex API
API_BASE_URL = "https://api.beyonnex.io"
API_ROOMS_ENDPOINT = "/homer/v2/rooms"
API_DEVICES_ENDPOINT = "/homer/v2/devices"
API_ROOM_TEMPERATURE_ENDPOINT = "/homer/rooms/{room_id}/temperature"
API_ROOM_OPEN_WINDOW_ENDPOINT = "/homer/rooms/{room_id}/openWindowDetection"
API_ROOM_GROUPS_ENDPOINT = "/resident-data/api/v1/room-groups"
API_ROOM_NAMES_ENDPOINT = "/resident-data/api/v1/room-groups/{group_id}/room-names"
API_ROOM_GROUP_PROFILE_ENDPOINT = (
    "/resident-data/api/v1/room-groups/{group_id}/profile"
)
API_SCHEDULER_STATE_ENDPOINT = "/homer/schedulers/{room_id}/state"
API_DEVICE_CHILD_LOCK_ENDPOINT = "/homer/devices/{device_eui}/childLock"

# AWS Cognito
COGNITO_USER_POOL_ID = "eu-central-1_OQPAAY4lb"
COGNITO_CLIENT_ID = "7r3k7jf5a5eg23cu275ha3vbi5"
COGNITO_REGION = "eu-central-1"

# Polling
DEFAULT_POLL_INTERVAL = 60  # seconds
POLL_JITTER = 15  # +/- seconds

# Temperature limits (from API observations)
MIN_TEMPERATURE = 6.0  # frost protection / off
MAX_TEMPERATURE = 28.0

# Config keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REFRESH_TOKEN = "refresh_token"
