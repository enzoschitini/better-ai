import firebase_admin
from firebase_admin import credentials, storage

# Initialize Firebase Admin SDK with your service account key
cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
   'storageBucket': 'your-project-id.appspot.com' # Replace with your bucket name
})

# Get a reference to the storage bucket
bucket = storage.bucket()

# Specify the file to upload and its destination in the bucket
local_file_path = "path/to/local/file.txt"
blob = bucket.blob("folder_in_bucket/file.txt") # Destination path in the bucket

# Upload the file
blob.upload_from_filename(local_file_path)
print("File uploaded successfully!")