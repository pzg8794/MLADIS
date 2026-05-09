from storages.backends.gcloud import GoogleCloudStorage


class PublicMediaStorage(GoogleCloudStorage):
    default_acl = None
    file_overwrite = False
    querystring_auth = False