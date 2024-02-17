from datetime import datetime, timezone
import os


class LoggerService:
    def log(self, message: str, show_datetime: bool = True, file_endline: str = '\n\n', print_endline: str = '\n\n'):
        now = datetime.now(tz=timezone.utc)
        log_filename = f"{now.strftime('%Y-%m-%d')}.txt"
        log_file_path = f"logs/{log_filename}"

        if (os.path.isfile(log_file_path) == False):
            f = open(log_file_path, "w")
            f.write("")
            f.close()

        print_message = f"{now.isoformat()}: {message}"
        file_message = f"{print_message}\n\n"

        if (show_datetime == False):
            print_message = message
            file_message = f"{print_message}{file_endline}"

        f = open(log_file_path, "a")
        f.write(file_message)
        f.close()
        print(print_message + print_endline)
