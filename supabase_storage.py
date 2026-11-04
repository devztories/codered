from storages.backends.s3 import S3Storage
from django.conf import settings


class SupabasePublicStorage(S3Storage):
    """Upload through Supabase S3 and return the public object URL."""

    def url(self, name, parameters=None, expire=None, http_method=None):
        name = str(name).lstrip("/")
        location = (self.location or "").strip("/")

        if location:
            prefix = location + "/"
            if name.startswith(prefix):
                name = name[len(prefix):]

        object_path = "/".join(
            part.strip("/") for part in (location, name) if part
        )

        return (
            f"{settings.SUPABASE_PUBLIC_URL}"
            f"/storage/v1/object/public/"
            f"{self.bucket_name}/{object_path}"
        )
