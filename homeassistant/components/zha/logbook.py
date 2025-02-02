"""Describe ZHA logbook events."""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from homeassistant.components.logbook.const import (
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.const import ATTR_COMMAND, ATTR_DEVICE_ID
from homeassistant.core import Event, HomeAssistant, callback
import homeassistant.helpers.device_registry as dr

from .core.const import DOMAIN as ZHA_DOMAIN, ZHA_EVENT
from .core.helpers import async_get_zha_device

if TYPE_CHECKING:
    from .core.device import ZHADevice


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Describe logbook events."""
    device_registry = dr.async_get(hass)

    @callback
    def async_describe_zha_event(event: Event) -> dict[str, str]:
        """Describe zha logbook event."""
        device: dr.DeviceEntry | None = None
        device_name: str = "Unknown device"
        zha_device: ZHADevice | None = None
        event_data: dict = event.data
        event_type: str | None = None
        event_subtype: str | None = None

        try:
            device = device_registry.devices[event.data[ATTR_DEVICE_ID]]
            if device:
                device_name = device.name_by_user or device.name or "Unknown device"
            zha_device = async_get_zha_device(hass, event.data[ATTR_DEVICE_ID])
        except (KeyError, AttributeError):
            pass

        if (
            zha_device
            and (command := event_data.get(ATTR_COMMAND))
            and (command_to_etype_subtype := zha_device.device_automation_commands)
            and (etype_subtypes := command_to_etype_subtype.get(command))
        ):
            all_triggers = zha_device.device_automation_triggers
            for etype_subtype in etype_subtypes:
                trigger = all_triggers[etype_subtype]
                if not all(
                    event_data.get(key) == value for key, value in trigger.items()
                ):
                    continue
                event_type, event_subtype = etype_subtype
                break

        if event_type is None:
            event_type = event_data[ATTR_COMMAND]

        if event_subtype is not None and event_subtype != event_type:
            event_type = f"{event_type} - {event_subtype}"

        event_type = event_type.replace("_", " ").title()

        message = f"{event_type} event was fired"
        if event_data["params"]:
            message = f"{message} with parameters: {event_data['params']}"

        return {
            LOGBOOK_ENTRY_NAME: device_name,
            LOGBOOK_ENTRY_MESSAGE: message,
        }

    async_describe_event(ZHA_DOMAIN, ZHA_EVENT, async_describe_zha_event)
