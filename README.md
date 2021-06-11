# Description
This action allows you to automatically create an issue on a reviewer's Linear/Jira board when a reviewer is added to a pull request with a '📦 dependencies' label. 

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
