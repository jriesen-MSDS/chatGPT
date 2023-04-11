import requests

# Specify the URL of the SharePoint 2016 site
site_url = "https://your-site-url.com"

# Specify the name of the SharePoint 2016 document library
doc_library_name = "Documents"

# Specify the path and name of the file to upload
file_path = "C:\\files\\file_to_upload.docx"

# Specify the SharePoint 2016 username and password
username = "your_username"
password = "your_password"

# Authenticate to the SharePoint site
auth = requests.auth.HTTPBasicAuth(username, password)

# Get the form digest value for the SharePoint site
response = requests.post(site_url + "/_api/contextinfo", auth=auth)
form_digest = response.json()["d"]["GetContextWebInformation"]["FormDigestValue"]

# Upload the file to the SharePoint site
with open(file_path, "rb") as file:
    file_contents = file.read()
    response = requests.post(
        site_url + f"/_api/web/lists/GetByTitle('{doc_library_name}')/RootFolder/Files/Add(url='{file_path}',overwrite=true)",
        data=file_contents,
        headers={
            "X-RequestDigest": form_digest,
            "accept": "application/json;odata=verbose",
            "content-type": "application/octet-stream"
        },
        auth=auth
    )

# Check the response status code for success or failure
if response.status_code == requests.codes.ok:
    print("File uploaded successfully")
else:
    print("File upload failed")
    print(response.json())
