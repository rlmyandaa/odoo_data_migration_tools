import pytz
from datetime import datetime
from odoo.tools.config import config


def do_convert_time(data):
    datetime_str = data.get('scheduled_running_time')
    if datetime_str:
        datetime_format = "%Y-%m-%d %H:%M:%S"
        datetime_obj = datetime.strptime(datetime_str, datetime_format)

        # Get current timezone from config
        server_timezone = config.get('timezone') or 'UTC'
        server_datetime = pytz.timezone(
            server_timezone).localize(datetime_obj)

        utc_datetime = server_datetime.astimezone(
            pytz.utc).replace(tzinfo=None)
        data['scheduled_running_time'] = utc_datetime.strftime(
            datetime_format)


def convert_datetime_data(vals):
    if isinstance(vals, list):
        for data in vals:
            do_convert_time(data)
    elif isinstance(vals, dict):
        do_convert_time(vals)
