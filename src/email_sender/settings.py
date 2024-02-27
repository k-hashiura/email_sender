from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, SecretStr


class Settings(BaseSettings):
    send_list_sheetname: str = "Sheet1"

    from_name: str
    from_address: EmailStr
    email_subject: str

    be_username: str
    be_api_key: SecretStr
    be_password: SecretStr

    txt_template: str = "./templates/template.txt.j2"
    html_template: str = "./templates/template.html.j2"

    model_config = SettingsConfigDict(env_file=".env")


def load_settings() -> Settings:
    return Settings()  # type: ignore
