import os
def push_config(request):
    return {"VAPID_PUBLIC_KEY": os.getenv("VAPID_PUBLIC_KEY", "")}
