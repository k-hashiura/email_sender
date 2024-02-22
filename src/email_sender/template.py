from jinja2 import Environment, FileSystemLoader, StrictUndefined

from logging import getLogger

from email_sender.settings import load_settings

settings = load_settings()
logger = getLogger(__name__)


def load_template():
    env = Environment(loader=FileSystemLoader("."), undefined=StrictUndefined)
    try:
        txt_template = env.get_template(settings.txt_template)
        html_template = env.get_template(settings.html_template)
    except Exception as e:
        logger.exception(e)
        exit()
    return txt_template, html_template
