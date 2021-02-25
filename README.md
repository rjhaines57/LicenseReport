# LicenseReport

This tool will generate a list of all projects and there license risk. It generates a CSV file that can be imported into other tools such as excel.

## Usage

LicenseReport.py --file <output file> \[--url <instance url>\]
Where:
    --file <filename> - Where filename is the name of the csv output file
    --url <url> - OPTIONAL - Url of the instance, e.g https://<company>.blackduck.synopys.com. This is used to generate a URL to point towards the project version in the BD interface
    
## Setup

Parameters for connecting to reporting database need to added to the database.init file stored with the repo.
Details of the values of these will be be specific to your instance. The values and the certificate files are available from Synopsys support

<pre>
[postgresql]
host=\<hostname\>
database=bds_hub
user=\<database_user\>
password=\<database_password\>
port=55436
sslcert=\<cert file name\>
sslkey=\<cert key file name\>
sslrootcert=\<root cert file name\>
sslmode=verify-ca
options=-c search_path=reporting
</pre>


