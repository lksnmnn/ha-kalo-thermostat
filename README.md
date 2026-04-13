# KALO Thermostat for Home Assistant

A custom Home Assistant integration for **KALO Smart Home** thermostats (powered by beyonnex.io).

KALO thermostats communicate via long-range radio (LoRaWAN), not Wi-Fi or Zigbee, so they can't be controlled locally. This integration connects to the KALO cloud API to provide thermostat control through Home Assistant.

## Features

-   Climate entities for each room (set target temperature, HVAC mode)
-   Temperature and humidity sensors for each thermostat device
-   Open window detection switch per room
-   Schedule switch per room (enable/disable heating schedule)
-   Child lock switch per thermostat device
-   Away mode switch per home (toggles between away and schedule profile)
-   Window open binary sensor per room
-   Room names fetched from the API (custom names set in the KALO app)
-   Smart polling with jitter to reduce server load
-   Disable polling via HA's built-in system option (useful for summer)
-   Reconfigure support for device remounting

## Installation

### Manual

1. Copy the `custom_components/kalo_thermostat` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services > Add Integration** and search for "KALO Thermostat".

### HACS (Custom Repository)

1. In HACS, go to **Integrations > Custom Repositories**.
2. Add this repository URL and select "Integration" as the category.
3. Install "KALO Thermostat" and restart Home Assistant.
4. Add the integration via **Settings > Devices & Services**.

## Configuration

Enter your KALO Smart Home account credentials (the same email and password you use in the KALO app).

## Entities

### Climate (per room)

-   **Current temperature** — average reading from all thermostats in the room
-   **Target temperature** — settable, range 6.0-28.0 C
-   **HVAC mode** — Heat or Off (Off sets target to 6.0 C frost protection)
-   **Humidity** — current room humidity

### Sensors (per device)

-   **Temperature** — individual thermostat temperature reading
-   **Humidity** — individual thermostat humidity reading

### Switches

-   **Open Window Detection** (per room) — enable/disable automatic open window detection
-   **Schedule** (per room) — enable/disable the heating schedule
-   **Child Lock** (per device) — lock/unlock the physical thermostat controls
-   **Away Mode** (per home) — toggle between away and schedule profile

### Binary Sensors

-   **Window Open** (per room) — indicates if the thermostat has detected an open window

## Disabling Polling (Summer Mode)

To stop API polling when heating is off, go to **Settings > Devices & Services > KALO Thermostat**, click the three-dot menu, select **System Options**, and disable **Enable polling**. Entities will keep their last known values. Re-enable when heating season starts.

## Reconfiguration

If thermostats are remounted or room assignments change:

1. Go to the integration entry in **Settings > Devices & Services**.
2. Click **Reconfigure** to re-enter credentials and reload all devices.
3. Alternatively, use the **Reload** button to refresh room/device mappings.

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or associated with KALO, beyonnex GmbH, or any of their subsidiaries. The API was reverse-engineered for personal interoperability purposes, which is permitted under EU Directive 2009/24/EC (Software Directive, Article 6) and German copyright law (UrhG Section 69e).

Use at your own risk. The API may change without notice.

## License

MIT License. See [LICENSE](LICENSE) for details.
