import os
import sys
from google.cloud import storage

def upload_folder(bucket_name, source_dir, run_id):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    print(f"Uploading {source_dir} to gs://{bucket_name}/{run_id}/")

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, source_dir)
            blob_path = f"{run_id}/{relative_path}"
            
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            print(f"  Uploaded: {blob_path}")

if __name__ == "__main__":
    bn = os.getenv("GCS_BUCKET")
    rid = os.getenv("RUN_ID", "experiment_unnamed")
    
    if bn:
        upload_folder(bn, "/app/results", rid)
    else:
        print("BŁĄD: Zmienna GCS_BUCKET nie jest ustawiona. Pomijam upload.")