import requests
from datetime import datetime, timedelta
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv
import os

class Submission:
    def __init__(self, id: int, title: str, timestamp: str):
        self.id = id
        self.title = title
        self.timestamp = timestamp

class API:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

class FormsAPI(API):

    def submit(self, username: str, solved: str):

        # Go back one day since this runs at around 4am
        time_before = datetime.now() - timedelta(days=1)
        year = time_before.strftime("%Y")
        month = time_before.strftime("%m")
        day = time_before.strftime("%d")

        payload = {
            "entry.351549347": username,
            "entry.1814219555": solved,
            "entry.672843189_year": year,
            "entry.672843189_month": month,
            "entry.672843189_day": day,
        }

        requests.post(self.endpoint, data=payload)



class SubmissionsAPI(API):

    def get_ac_submissions(self, username: str, limit: int = 15) -> List[Submission]:
        query = '''
          query recentAcSubmissions($username: String!, $limit: Int!) {
            recentAcSubmissionList(username: $username, limit: $limit) {
              id
              title
              timestamp
            }
          }
        '''

        variables = {
            "username": username,
            "limit": limit
        }

        payload = {
            "query": query,
            "variables": variables,
            "operationName": "recentAcSubmissions"
        }

        response = requests.post(self.endpoint, json=payload)
        response_json = response.json()

        if "data" in response_json and "recentAcSubmissionList" in response_json["data"]:
            submission_list = response_json["data"]["recentAcSubmissionList"]
            submissions = [
                Submission(submission["id"], submission["title"], submission["timestamp"])
                for submission in submission_list
            ]
            return submissions
        else:
            raise APIError("Failed to retrieve submissions from the API.")

    def count_submissions_in_past_day(self, username: str) -> int:
        submissions = self.get_ac_submissions(username)
        filtered_submissions = [
            submission for submission in submissions
            if self._within_hours(submission.timestamp, 24)
        ]
        return len(filtered_submissions)

    @staticmethod
    def _within_hours(timestamp: str, hours: int = 24) -> bool:
        current_time = datetime.now()
        provided_time = datetime.fromtimestamp(int(timestamp))
        time_difference = current_time - provided_time
        return time_difference <= timedelta(hours=hours)

class APIError(Exception):
    pass

def main():

    load_dotenv()

    submissions_api = SubmissionsAPI("https://leetcode.com/graphql")
    forms_api = FormsAPI(os.environ.get('GOOGLE_FORMS_RESPONSE_URL'))

    names_file = os.environ.get("NAMES_FILE")
    usernames = []
    with open(names_file, "r") as file:
        usernames = [name.strip() for name in file]

    for username in tqdm(usernames):
        try:
            solved = submissions_api.count_submissions_in_past_day(username)
            forms_api.submit(username, solved)
            print(f"\nUploaded {username}")
        except APIError as e:
            print(f"API Error: {str(e)}")

    print("All uploaded")


if __name__ == "__main__":
    main()
