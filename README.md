# Dependabot PR Issue Creator
This action allows you to automatically create an issue on a reviewer's Linear/Jira board when a reviewer is added to a pull request. 

# Setup
Before the action can be used properly, the following Github secrets must be created on the repository: 
<br>
* GITHUB_TOKEN
* JIRA_API_EMAIL
* JIRA_API_TOKEN
* LINEAR_API_TOKEN
<br>

In addition, the `CONFIG_FILE` environment variable within the action.yml file must be pointed to the path of the config file (default path is reviewers-info.json), and its contents must be populated with the appropriate reviewer information. An example of the file format can be found in this repository at ".github/reviewers-info.json". 

For Jira, obtaining the information is quite simple. For the project key, you can navigate to the team's project board. For user Jira ID's, you can navigate to that user's profile. In both cases, the desired information can be found at the end of the URL. 

For Linear, the simplest way to obtain the project and user IDs is through the Linear API. Examples of how to query team IDs and user IDs can be found here: https://developers.linear.app/docs/graphql/working-with-the-graphql-api

# Usage

```
on:
  pull_request:
    branches: [ next ]
    types: [ review_requested ]

jobs:
  create-issue:
    if: contains( github.event.pull_request.labels.*.name, '📦 dependencies' )
    env: 
      CONFIG_FILE: .github/reviewers-info.json
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        
      - name: Setup Python
        uses: actions/setup-python@v2
        
      - name: install requests
        run: pip install requests
        
      - name: Create Issue
        run: |
          if [ ${{ env.WHICH }} == "JIRA" ]
          then
            python ./bin/create-issue-from-dependency-PR/create-jira-ticket.py -e $GITHUB_EVENT_PATH -u $JIRA_API_EMAIL -p $JIRA_API_TOKEN -config ${{ env.CONFIG_FILE }} -gt ${{ env.GITHUB_TOKEN }} -ref $GITHUB_REF
          elif [ ${{ env.WHICH }} == "LINEAR" ]
          then
            python ./bin/create-issue-from-dependency-PR/create-linear-issue-for-dependencies-pr.py -e $GITHUB_EVENT_PATH -p $LINEAR_API_TOKEN -config ${{ env.CONFIG_FILE }} -gt ${{ env.GITHUB_TOKEN }} -ref $GITHUB_REF
          fi
        env: 
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          JIRA_API_EMAIL: ${{ secrets.JIRA_API_EMAIL }}
          LINEAR_API_TOKEN: ${{ secrets.LINEAR_API_TOKEN }} 
          WHICH: LINEAR
```

# Description

## Why it's useful 
When a dependencies pull request is created, a member from the front end team is randomly assigned as a reviewer for the pull request. The reviewer will be notified through GitHub, but a corresponding ticket won’t be automatically created on their Linear/Jira board. This can lead to the pull request getting picked up very slowly if at all, and this is especially problematic when the pull request needs to be addressed a little more urgently, such as when it's a security update.

This project solves this problem by triggering a workflow that automatically generates an issue on the reviewer's Linear/Jira board whenever a dependencies update pull request is created. This will hopefully solve visibility issues and will lead to those pull requests getting picked up more promptly. 

## How it works
The dependabot PR issue creator makes use of github actions to trigger on a request for review of a pull request with the "📦 dependencies" label (but can be configured to any label), and proceeds in the following steps: 
1. Reads the file containing the webhook event payload, and extracts the necessary information from the pull request to create the Linear/Jira ticket.
2. Fetches the config file containing the information of the pull request reviewers such as what team they belong to and their Linear/Jira ID. The default location of this file is at ".github/reviewers-info.json", and an example of it's format can be found at that path in this repository. 
3. Before creating a ticket on someone's board, the action will check whether that ticket already exists by searching the board for a description containing the URL to the pull request. This is necessary to prevent duplicate tickets in the case that a reviewer is requested, reviews the pull request, then is re-requested again to review the same pull request.
4. If the ticket does not already exist, then the action will create the issue on the reviewer's board.
5. If creating a jira ticket, then after creating the issue, the issue will be transitioned into the appropriate workflow state if not already there.

# requirements
the path to the config file, the config file format and example
how to grab jira project id, individual id
linear project id (API), individual id (API)
everything they need to make sure it's setup
create a label, and set the yml file

How to set up the config file 
To obtain Jira project ID and individual ID. 


# example usage

