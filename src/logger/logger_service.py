from datetime import datetime, timezone
import os


class LoggerService:
    def log(self, message: str):
        now = datetime.now(tz=timezone.utc)
        log_filename = f"{now.strftime('%Y-%m-%d')}.txt"
        log_file_path = f"logs/{log_filename}"

        if (os.path.isfile(log_file_path) == False):
            f = open(log_file_path, "w")
            f.write("")
            f.close()

        f = open(log_file_path, "a")
        f.write(
            f"{now.isoformat()}: {message}\n\n")
        f.close()
        print(f'{now.isoformat()}: {message}')
