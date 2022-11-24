
import asyncio
import time
from typing import Any
from datetime import timedelta
from functools import lru_cache
import logging
import aiohttp

from .const import DOMAIN, CONFIG_TOKEN, CONFIG_TOPIC, CONFIG_URL

from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers import state as state_helper
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant import const


_LOGGER = logging.getLogger(__name__)
INTERVAL = timedelta(seconds=30)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    cfg = config[DOMAIN]
    warp10 = Warp10Logger(cfg)
    hass.bus.async_listen(const.EVENT_STATE_CHANGED,warp10.event_handler)
    async_track_time_interval(hass, warp10.periodic_push, INTERVAL)
    return True


class Warp10Logger(object):
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.data = []
        self.lock = asyncio.Lock()

    async def event_handler(self, event: Event):
        entity_id = event.data.get('entity_id')
        entity_platform = entity_id.split('.')[0]
        new_state =  event.data.get('new_state')
        if new_state is None:
            return
        try:
            state_value = float(state_helper.state_as_number(new_state))
        except ValueError:
            return

        attributes = new_state.attributes
        now = round(time.time() * 1000000)
        tags  = '{entity_id=%s}' % entity_id
        line = None
        if entity_platform == 'sensor':
            # a lot of sensors does provide an device_class :( same issue already reported
            # to ESPHome. We only can trust units
            if 'unit_of_measurement' in attributes.keys() :
                unit =  attributes.get('unit_of_measurement','')
                fake_class = get_unit_name(unit)
                if fake_class==None:
                    # WARNING: sensor without unit will not be reported
                    return
                name = self.cfg[CONFIG_TOPIC] + '.sensor_' + fake_class
                line = "%s// %s%s %s" % (now,name,tags,state_value)
        else:
            # Everything else is in an entity_platform TS. 
            state_value = int(state_value)
            name = self.cfg[CONFIG_TOPIC] + '.' + entity_platform
            line = "%s// %s%s %s" % (now,name,tags,state_value)

        if line:
            async with self.lock:
                self.data.append(line)

    async def periodic_push(self, now=None):
        buf = ''
        async with self.lock:
            buf = '\n'.join(self.data)
            self.data = []

        if len(buf) > 0:
            session = aiohttp.ClientSession()
            try:
                await session.post(self.cfg[CONFIG_URL],headers={'X-Warp10-Token':self.cfg[CONFIG_TOKEN]},data=buf)
                await session.close()
            except aiohttp.ClientConnectorError:
                _LOGGER.error("Failed to push data")


@lru_cache(128)
def get_unit_name(value: str):
    # HASS doesn't have a reverse map, units (as string) to unit Enum
    # so, used this uggly trick. 
    for k,v in const.__dict__.items():
        if v == value:
            return k.lower()


