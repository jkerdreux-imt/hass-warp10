# Warp10 Logger for Home Assistant

This integration platform stores all entity states in [Warp10](https://www.warp10.io/) time series.

    
## Install
Just copy this repository in your custom_component folder:

    git clone https://github.com/jkerdreux-imt/hass-warp10.git ~/.homeassistant/custom_components/warp10/


## Configuration
Edit your *configuration.yaml* file and add the following items:

    warp10:
        url: http://localhost:8080/api/v0/update
        token: XXXXXXXXXXXXXXXXXXX
        topic: hass.dev


## Notes
Some Home Assistant devices do not support *device_class* right now. Time series should be named from this. I used the same trick as InfluxDB logger. Each TS uses a name forged from its entities units (sensors) or platform.

Here some sensors: 

    hass.dev.sensor_energy_kilo_watt_hour
    hass.dev.sensor_temp_celsius
    ...

For anything else:

    hass.dev.light
    hass.dev.siren
    hass.dev.binary_sensor
    ...

Some integration platforms (MQTT ie) set a default value to zero for each entity at startup, so you should have some noise in your TS if you restart HA too often.

The configuration check is missing right now, so expect some tracebacks if you mess the config file.