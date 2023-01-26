# RarePepeWorld.com Notes

These are the files used to run a website for displaying Pepe cards created on the Counterparty network.
It was written in Python 3 using the Flask framework. See https://flask.palletsprojects.com/en/2.2.0/

## Code Files

The following code paths/files are part of this repo:

`RarePepeWorld/rpw/` → base path of code

`run.sh_live`, `run.sh_local`, `run.sh_testing`, etc. → scripts that launch the webserver. The different versions were
created to enable having different edits for different server run contexts. (e.g. local testing server)

`Settings.py`, `Settings.py_live`, `Settings.py_local`, `Settings.py_testing`, etc → Files for setting various values
for running the server.
The different versions to enable having different edits for different server run contexts. Copy the particular context to
Settings.py for the particular server that will be run

`requirements.txt` → python pip packages to install for the site to be able to run.
Must be installed in the python virtual environment of the running server. See 
https://docs.python.org/3/tutorial/venv.html and below.

`update_live.sh` → Script that was used to copy files to be deployed for the live server.

`static/` → Various unchanging files for the running site

`static/css` --> css style files

`static/data` --> various saved data: burn addresses, faq questions list, etc

`static/js` --> Javascript files

`static/sql` → Mysql database related files

`static/images`, `static/pepes`, `static/qr` → symbolic links to image files. They were stored outside of repo

`/home/rpw/RarePepeWorld/rpw/static/sql/CounterpartyPepes.sql` → base sql database setup

`templates/` → template files for determining the display of the website pages, described below

`script_building/` → various scripts and files that were used for testing aspects of the website and backend

`tools/` → various scripts for completing necessary tasks, like updating the database

`tools/db_fill_asset_series_numbers.py`, `db_fill_burn_addresses.py`, `db_fill_image_file_names.py`,
`db_fill_real_supply.py`, `db_fill_source_addresses.py`, `db_generate_rarepepedirectory_urls.py`
, `db_insert_pepe_data.py`
→ scripts for populating the database with required data. As the site was expanded, new db entries were needed to be
created

`toos/db_populate_cp.sh`, `tools/db_populate_xchain` → scripts for updating the database on the fly via a CounterParty
node and XChain site as data source, respectively

`toos/price_updater.py` → script for maintaining the price on the fly

`Logging.py` → Classes for directing log messages to various files/outputs

`QueryTools.py` → Classes for managing data pertaining to various elements of the site: XChain site, Counterparty node,
Pepe details from the database, price lookups, btcpayserver, etc

`ViewsData.py` → Classes for prepping the data before it is passed to the Flask templates

`DataConnectors.py` → Lower level data access to the information sources: Mysql database queries, Xchain queries,
Counterparty rpc queries, btcpayserver queries

`Utils.py` → some tools for miscellaneous requirements: json file processing, qr code creation, pagination of lists

`app.py` → Flask entry point to the site. Determines how urls are rendered, triggers desired templates and components
required to display pages.

## Flask Templates

* display of site pages determined by Flask templates in the `/templates/` folder
* the python code passes the data to the template and are accessed as variables in the template file
* How the templating system works can be found in this
  documentation: https://flask.palletsprojects.com/en/2.2.x/tutorial/templates/

## To Run the site

In the base setup that was used, a Python environment was created, with Flask and other necessary packages installed.

### Python Run Environment

A python environment was created via:

    # python3 -m pip install --user virtualenv

See https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

The virtual environment can be created at the desired path, e.g. .venv, in the path where the server files are 
installed.

```# python3 -m venv .venv```

To activate the virtual environment:

```# source .venv/bin/activate```

Inside the virtual environment, install required packages via pip:

```# pip install -r requirements.txt```

### Local Run

To run local, the run.sh_testing script gives an example command sequence.

### Nginx/Gunicorn

To run via external domain, Nginx/Gunicorn can provide this functionality:

* Nginx forwards requests to gunicorn via the Nginx site defined in the sites-available configuration
    * Relevant config files: `/etc/nginx/nginx.conf` `/etc/nginx/sites-available/<site_domain>`
* For description of this arrangment, see
  https://docs.gunicorn.org/en/stable/deploy.html,
  https://flask.palletsprojects.com/en/2.2.0/deploying/gunicorn/

The run.sh_live completed the launch process as follows:

* Activates python environment
* changes to the path where the live site files are stored. Say, ```/var/www/rpw/run/RarePepeWorld/```
* Sets some variables
* Launches WSGI HTTP server, Gunicorn:
  `# gunicorn -b 127.0.0.1:8000 "rpw.app:create_app()"`
    * gunicorn starts the Flask code that determines how the server responds to requests to the website
    * entry point is in `/var/www/rpw/run/RarePepeWorld/rpw/app.sh`
    * launches the `create_app()` method

### Persistence: Byobu/Tmux/Pm2

* To keep the server running persistently some kind of service manager is needed. Pm2 is good choice.
* Byobu/tmux can keep services running persistently as well.
* See https://byobu.org/, https://github.com/tmux/tmux, or https://pm2.io/.

## Database

To store the data for the site, Mysql was used.

### User

A user with the credentials in the Settings.py file needs to exist.

```# sudo mysql -p```

```# mysql> CREATE USER 'cp'@'localhost' IDENTIFIED BY 'password';```

To populate data with the required tables, the base db structure is available in rpw/static/sql/CounterpartyPepes.sql.

Database privileges must be given to the user in Settings.py:

```# mysql> GRANT ALL PRIVILEGES ON CounterpartyPepes TO 'cp'@'localhost' # mysql> FLUSH PRIVILEGES;```

See https://www.digitalocean.com/community/tutorials/how-to-create-a-new-user-and-grant-permissions-in-mysql, 
https://dev.mysql.com/doc/refman/5.7/en/create-user.html, 
https://dev.mysql.com/doc/refman/5.7/en/reloading-sql-format-dumps.html,
or https://dev.mysql.com/doc/refman/5.7/en/mysqldump-sql-format.html


## Resources

### Counterparty

Main site: https://counterparty.io/

Docs main: https://counterparty.io/docs/

Protocol specification: https://counterparty.io/docs/protocol_specification/

API: https://counterparty.io/docs/api/

### XChain

Main site: https://www.xchain.io/

API: https://www.xchain.io/api

### Pepes

RarePepe Directory: http://rarepepedirectory.com/

RarePepeWorld Live site: https://rarepepeworld.com/
