import time
import traceback
from src.utils.unique_id_factory import IDGenerator
from src.web_services_network.auth import Authorization

class RequestResorse:
    def __init__(self):
        self.jobId = IDGenerator.timestamp(prefix="job_")
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def _finalize(self):
        self.end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.duration = time.mktime(time.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"))

    def success_response(self, result):
        self._finalize()
        return {
            "jobId": self.jobId,
            "status": "success",
            "status_code": 200,
            "result": result,
            "time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration_seconds": self.duration
            }
        }
    
    def error_response(self, error):
        self._finalize()
        return {
            "jobId": self.jobId,
            "status": "error",
            "status_code": 500,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            },
            "time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration_seconds": self.duration
            }
        }
