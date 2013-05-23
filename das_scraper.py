from BeautifulSoup import BeautifulSoup
import re
import requests
import sys

DAS_BASE_URL='https://www.destroyallsoftware.com/'
SIGN_IN_URI=DAS_BASE_URL+'/screencasts/users/sign_in'
CATALOG_URI=DAS_BASE_URL+'/screencasts/catalog'

USER_EMAIL='foo@domain.com'
USER_PASSWORD='password'

# Load the sign_in page
try:
    r = requests.get(SIGN_IN_URI, verify=True)
except:
    print "Could not load sign_in page"
    sys.exit(1)

# Grab the CSRF Token
form_token = re.search('content="(.*)" name="csrf-token"', r.content).group(1)

# Populate the form data and POST to the SIGN_IN_URL
post_data = {'authenticity_token': form_token,
             'user[email]': USER_EMAIL,
             'user[password]': USER_PASSWORD,
             'user[remember_me]': 0,
             'commit': 'Sign in'}

r = requests.post(SIGN_IN_URI, verify=True, data=post_data)

# Grab response cookies, specifically for the session id
set_cookies = r.headers['set-cookie']
session_id = re.search('_destroyallsoftware_session=([^;]*);', set_cookies).group(1)

# Populate our headers with the session id
session_header = {'Cookie': '_destroyallsoftware_session={0}'.format(session_id)}

# Grab the catalog listing of all the screencasts
r = requests.get(CATALOG_URI, verify=True, headers=session_header)

# Stop if we cannot parse the contents of the catalog
try:
    soup = BeautifulSoup(r.content)
except:
    print "Unable to parse HTML from Catalog"
    sys.exit(1)

# Grab all of the anchor tags and populate a list
all_links = soup.findAll('a')

# Iterate through the list of tags and pull out the name of the screencast if it exists
download_uris = []
for link in all_links:
    try:
        uri = re.search('(screencasts/catalog/[^"]*)', link.attrs[0][1]).group(0)
    except:
        continue 
    download_uri = '{0}/download'.format(uri)
    download_uris.append(download_uri)

# Download, in serial, the screencast in high quality for each of the download_uris
for uri in download_uris:
    filename = uri.split('/')[2]
    try:
        # Don't overwrite existing screencasts
        with open('{0}.mov'.format(filename)): continue
    except:
        download_url = "{0}{1}".format(DAS_BASE_URL,uri)
        print download_url
        print filename
        # Write the screencast to a file (e.g. git-workflow.mov)
        with open('{0}.mov'.format(filename), 'wb') as handle:
            r = requests.get(download_url, verify=True, headers=session_header, stream=True)
            for block in r.iter_content(1024):
                if not block:
                    break
                handle.write(block)

