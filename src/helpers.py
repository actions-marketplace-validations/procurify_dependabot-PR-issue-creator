import os
import json
import requests
import base64

def get_pull_request_info(event_file_path):
    if not os.path.isfile(event_file_path):
        raise Exception("Couldn't find github event file")

    with open(event_file_path) as file:
        event_obj = json.loads(file.read())
    
    res = {
        "reviewers": event_obj["pull_request"]["requested_reviewers"],
        "title": event_obj["pull_request"]["title"],
        "number": event_obj["pull_request"]["number"],
        "url": f"https://github.com/procurify/procurify-react/pull/{event_obj['pull_request']['number']}"
    }
    return res

def create_issue_info(pr_info):
    issue_title = f"Review dependencies pull request: {pr_info['title']}"
    issue_description = f"{pr_info['title']}: {pr_info['url']}"
    return {"title": issue_title, "description": issue_description}
    
def fetch_reviewers_info(file_path, github_token, github_ref):

   headers = {
      'Accept': 'vnd.github.v3+json',
      'Authorization': f'token {github_token}'
   }

   response = requests.get(
      f'https://api.github.com/repos/procurify/procurify-react/contents/{file_path}?ref={github_ref}', 
      headers=headers
   )
   contents = response.json()["content"]
   decoded = base64.b64decode(contents)
   all_reviewers_info = json.loads(decoded)

   return all_reviewers_info

   

def get_reviewer_linear_info(reviewers_info, reviewer):
    username = reviewer["login"]
    return reviewers_info[username]["linear"]

def get_reviewer_jira_info(reviewers_info, reviewer):
    username = reviewer["login"]
    return reviewers_info[username]["jira"]

def check_if_linear_issue_exists(team_id, pr_url, api_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_token,
    }

    query = """query {{
  team(id: "{team_id}") {{
    id
    name
    issues {{
      nodes {{
        id
        title
        description
      }}
    }}
  }}
}}""".format(team_id=team_id)

    unparsed_response = requests.post('https://api.linear.app/graphql', headers=headers, json={"query": query})

    response = unparsed_response.json()
    issues = response["data"]["team"]["issues"]["nodes"]
    issue_exists = False
    for issue in issues:
        if issue["description"] and pr_url in issue["description"]:
            issue_exists = True
    return issue_exists

def fetch_most_appropriate_workflow_state(team_id, api_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_token,
    }

    query = """query {
  workflowStates(first: 200) {
    nodes {
      id
      name
      type
      team {
        id
        name
      }
    }
  }
}"""
    response = requests.post('https://api.linear.app/graphql', headers=headers, json={"query": query})
    states = response.json()["data"]["workflowStates"]["nodes"]
    # order of preference, the larger the better
    states_to_preference = {"Inbox": 2, "Accepted": 1, "Todo": 1, "To do": 1, "Backlog": 0, "": -1}
    state_name = ""
    state_id = ""
    for state in states:
        if (state["name"] in states_to_preference.keys() and 
                state["team"]["id"] == team_id and 
                states_to_preference.get(state["name"], -1) > states_to_preference[state_name]):
            state_id = state["id"]
            state_name = state["name"]
    return state_id


def create_linear_issue(title, description, team_id, assignee_id, state_id, api_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_token,
    }

    query = """mutation {{
  issueCreate(
    input: {{
      title: "{title}"
      description: "{description}"
      teamId: "{team_id}"
      assigneeId: "{reviewer_id}"
      stateId: "{state_id}"
    }}
  ) {{
    success
    issue {{
      id
      title
    }}
  }}
}}""".format(title=title, description=description, team_id=team_id, reviewer_id=assignee_id, state_id=state_id)
    response = requests.post('https://api.linear.app/graphql', headers=headers, json={"query": query})
    return response

def check_if_jira_issue_exists(team_id, pr_url, auth):

   search_issue_url = "https://procurifydev.atlassian.net" + "/rest/api/3/search"

   params = {
      "jql": f'project={team_id} AND description ~ "{pr_url}"'
   }

   response = requests.request(
      "GET",
      search_issue_url,
      auth=auth,
      params=params
   )

   searched_issues = response.json()
   issue_exists = searched_issues["total"] > 0
   return issue_exists

def create_jira_issue(title, description, team_id, assignee_id, auth):
   issue_url = "https://procurifydev.atlassian.net" + "/rest/api/3/issue"

   headers = {
      "Accept": "application/json"
   }

   request_body = {
      "fields": {
         "project":
         {
            "key": team_id
         },
         "summary": title,
         "description": {
            "type": "doc",
            "version": 1,
            "content": [
                  {
                     "type": "paragraph",
                     "content": [
                        {
                              "type": "text",
                              "text": description
                        }
                     ]
                  }
            ]
         },
         "issuetype": {
            "name": "Task"
         },
         "assignee": {
            "id": assignee_id
         },
         "reporter": {
            "id": assignee_id
         }
      }
   }

   response = requests.request(
      "POST",
      issue_url,
      headers=headers,
      auth=auth,
      json=request_body
   )

   issue_key = json.loads(response.text)["key"]
   return issue_key

def transition_jira_issue(issue_key, auth):
   transitions_url = "https://procurifydev.atlassian.net" + f"/rest/api/3/issue/{issue_key}/transitions"

   response = requests.request(
      "GET",
      transitions_url,
      auth=auth,
   )

   transitions_response = json.loads(response.text)
   transitions = transitions_response["transitions"]
   triage_id = None
   for transition in transitions:
      if transition["name"] == "Triage":
         triage_id = transition["id"]

   if triage_id:
      update_json = {
         "transition": {
            "id": triage_id
         }
      }

      response = requests.request(
         "POST",
         transitions_url,
         auth=auth,
         json=update_json
      )
   else: 
      print("Triage was not found in transitions, doing nothing")