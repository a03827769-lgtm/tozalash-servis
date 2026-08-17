import urllib.request
import urllib.error
import os
import sys
import time

url = "https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp311-cp311-win_amd64.whl"
file_name = "torch-2.5.1_cu121.whl"


def download_file(url, filename):
    retries = 0
    max_retries = 100

    while retries < max_retries:
        try:
            if os.path.exists(filename):
                downloaded = os.path.getsize(filename)
            else:
                downloaded = 0

            req = urllib.request.Request(url)
            if downloaded > 0:
                req.headers["Range"] = f"bytes={downloaded}-"

            print(
                f"Connecting to server... (Resume from: {downloaded / 1024 / 1024:.2f} MB)"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status not in (200, 206):
                    print(f"Server returned HTTP {response.status}")
                    time.sleep(5)
                    retries += 1
                    continue

                total_size = int(response.headers.get("Content-Length", 0)) + downloaded

                # Check if fully downloaded
                if downloaded >= total_size and total_size > 0:
                    print("\nFile is already fully downloaded!")
                    return True

                mode = "ab" if downloaded > 0 else "wb"
                with open(filename, mode) as out_file:
                    while True:
                        buffer = response.read(2 * 1024 * 1024)  # 2MB chunks
                        if not buffer:
                            break
                        out_file.write(buffer)
                        downloaded += len(buffer)
                        print(
                            f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB",
                            end="",
                        )

                print("\nDownload complete!")
                return True

        except urllib.error.HTTPError as e:
            if e.code == 416:  # Range not satisfiable (file already fully downloaded)
                print("\nFile fully downloaded (HTTP 416).")
                return True
            print(f"\nHTTP Error: {e.code}. Retrying... ({retries}/{max_retries})")
            retries += 1
            time.sleep(3)
        except Exception as e:
            print(f"\nNetwork Error: {e}. Retrying... ({retries}/{max_retries})")
            retries += 1
            time.sleep(3)

    return False


if __name__ == "__main__":
    success = download_file(url, file_name)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
