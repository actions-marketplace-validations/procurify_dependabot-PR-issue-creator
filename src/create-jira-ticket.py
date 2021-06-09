import json
import sys
import os
import argparse
import requests
from requests.auth import HTTPBasicAuth
from helpers import (
   get_pull_request_info,
   create_issue_info,
   fetch_reviewers_info,
   get_reviewer_jira_info,
   check_if_jira_issue_exists,
   create_jira_issue,
   transition_jira_issue
)


parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", required=True)
parser.add_argument("-p", "--password", required=True)
parser.add_argument("-e", "--event", required=True)
parser.add_argument("-config", "--configuration", required=True)
parser.add_argument("-gt", "--github_token", required=True)
parser.add_argument("-ref", "--github_ref", required=True)

io_args = parser.parse_args()
JIRA_API_EMAIL = io_args.username
JIRA_API_TOKEN = io_args.password
event_path = io_args.event
config_filepath = io_args.configuration
github_token = io_args.github_token
github_ref = io_args.github_ref

pr_info = get_pull_request_info(event_path)

issue_info = create_issue_info(pr_info)

reviewers_info = fetch_reviewers_info(config_filepath, github_token, github_ref)

jira_auth = HTTPBasicAuth(JIRA_API_EMAIL, JIRA_API_TOKEN)

for reviewer in pr_info["reviewers"]:

   reviewer_info = get_reviewer_jira_info(reviewers_info, reviewer)

   issue_exists = check_if_jira_issue_exists(reviewer_info["project_key"], pr_info["url"], jira_auth)

   if not issue_exists:
      issue_key = create_jira_issue(
         issue_info["title"], 
         issue_info["description"], 
         reviewer_info["project_key"], 
         reviewer_info["jira_id"], 
         jira_auth
      )
      
      transition_jira_issue(issue_key, jira_auth)
   else:
      print("Issue already exists, skipping")
