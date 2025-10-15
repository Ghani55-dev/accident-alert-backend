from pyfcm import FCMNotification

# Add your Firebase Server Key
push_service = FCMNotification(api_key="YOUR_FIREBASE_SERVER_KEY")

def send_push_notification(title, message, registration_ids):
    result = push_service.notify_multiple_devices(
        registration_ids=registration_ids,
        message_title=title,
        message_body=message
    )
    return result
