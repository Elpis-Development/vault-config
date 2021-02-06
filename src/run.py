import concurrent.futures
import logging
import os
from logging.handlers import RotatingFileHandler

import click

from vault import VaultClient

log_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(message)s',
                                  datefmt='%d-%b-%y %H:%M:%S')
root_logger = logging.getLogger()

file_handler = RotatingFileHandler(filename="{0}/logs/app.log".format(os.environ["HOME"]),
                                   mode='w', maxBytes=10000, backupCount=1)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.ERROR)
# consoleHandler.setLevel(logging.INFO)
root_logger.addHandler(console_handler)


@click.group()
async def main():
    click.echo("Vault Init tool. Happy using!")
    pass


@main.command()
@click.option('--full-verbose', '-v', is_flag=True, default=False)
def init(full_verbose: bool = False):
    vault = VaultClient(full_verbose)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        if executor.submit(vault.init_vault).result() and executor.submit(vault.enable_secrets).result() \
                and executor.submit(vault.apply_policies).result() and executor.submit(vault.enable_auth).result():
            click.echo("Vault was initialized!")
        else:
            click.echo("Unable to initiate Vault.")


if __name__ == "__main__":
    main()
