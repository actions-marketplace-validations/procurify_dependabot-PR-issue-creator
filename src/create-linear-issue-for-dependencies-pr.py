import requests
import json
import os
import argparse
from helpers import (
    get_pull_request_info, 
    create_issue_info,
    fetch_reviewers_info, 
    get_reviewer_linear_info, 
    check_if_linear_issue_exists, 
    fetch_most_appropriate_workflow_state, 
    create_linear_issue
)

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--password", required=True)
parser.add_argument("-e", "--event", required=True)
parser.add_argument("-config", "--configuration", required=True)
parser.add_argument("-gt", "--github_token", required=True)
parser.add_argument("-ref", "--github_ref", required=True)


io_args = parser.parse_args()
LINEAR_API_TOKEN = io_args.password
event_path = io_args.event
config_filepath = io_args.configuration
github_token = io_args.github_token
github_ref = io_args.github_ref

pr_info = get_pull_request_info(event_path)

issue_info = create_issue_info(pr_info)

reviewers_info = fetch_reviewers_info(config_filepath, github_token, github_ref)

for reviewer in pr_info["reviewers"]:

    reviewer_info = get_reviewer_linear_info(reviewers_info, reviewer)

    issue_exists = check_if_linear_issue_exists(reviewer_info["project_key"], pr_info["url"], LINEAR_API_TOKEN)

    if issue_exists:
        print("Issue already exists")
    else: 
        state_id = fetch_most_appropriate_workflow_state(reviewer_info["project_key"], LINEAR_API_TOKEN)
        if not state_id:
            raise Exception("Could not find any workflow state")

        response = create_linear_issue(
            issue_info["title"], 
            issue_info["description"], 
            reviewer_info["project_key"], 
            reviewer_info["linear_id"], 
            state_id,
            LINEAR_API_TOKEN
        )
            
        print(f"CREATE ISSUE RESPONSE: {response.json()}")
        