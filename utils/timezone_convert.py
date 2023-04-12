import pytz
from datetime import datetime
from odoo.tools.config import config


def do_convert_time(datetime_str):
    datetime_format = "%Y-%m-%d %H:%M:%S"
    datetime_obj = datetime_str
    if isinstance(datetime_obj, str):
        datetime_obj = datetime.strptime(datetime_str, datetime_format)

    # Get current timezone from config
    server_timezone = config.get('timezone') or 'UTC'
    server_datetime = pytz.timezone(
        server_timezone).localize(datetime_obj)

    utc_datetime = server_datetime.astimezone(
        pytz.utc).replace(tzinfo=None)
    utc_datetime_str = utc_datetime.strftime(
        datetime_format)
    return utc_datetime_str


def convert_datetime_data(vals):
    if isinstance(vals, list):
        for data in vals:
            datetime_str = data.get('scheduled_running_time')
            if datetime_str:
                new_utc_datetime_str = do_convert_time(datetime_str)
                data['scheduled_running_time'] = new_utc_datetime_str
    elif isinstance(vals, dict):
        datetime_str = vals.get('scheduled_running_time')
        if datetime_str:
            new_utc_datetime_str = do_convert_time(datetime_str)
            vals['scheduled_running_time'] = new_utc_datetime_str
