from enum import Enum
import sys
import getpass
from typing import Any, Dict, List
from jira import JIRA
import jira.resources as jr
from github import Github

class JiraIssueType(Enum):
    Bug = "Bug"
    Story = "Story"
    Task = "Task"
    Epic = "Epic"

class JiraConn():
    class JIssue:
        def __init__(self, jissue: jr.Issue, jira_con: JIRA) -> None:
            self.jissue = jissue
            self.jira_con = jira_con

        def add_comment(self, comment):
            self.jira_con.add_comment(self.jissue.id, comment)

        def add_note(self, note):
            self.jira_con.add_issue_property

    def __init__(self, project) -> None:        
        #username=input("Enter Username for JIRA:")
        #password = getpass.getpass(prompt='Password: ', stream=None)
        self.project = project
        self.jira = JIRA(server='https://jira.devtools.intel.com/',
                max_retries=1,
                #basic_auth=(username, password),
                token_auth='',
                options={'verify': 'my.ca_bundle'})
        self.field_name_to_id = {}
        for f in self.jira.fields():
            self.field_name_to_id[f['name']] = f['id']
            #print(f['id'], f['name'])
            


    def assign(self, key, user):        
        issue = self.jira.issue(key)
        self.jira.assign_issue(issue, user)

    def translate_fileds(self, fields_dict) -> Dict[str, Any]:
        return dict( (self.field_name_to_id[key], val) for key,val in fields_dict.items())

    def create_issue(self, itype: JiraIssueType, title: str, body: str, source: str) -> jr.Issue: 
        return JiraConn.JIssue(
                self.jira.create_issue(fields = self.translate_fileds({
                                            'Project': {'key': self.project}, 
                                            'Issue Type' :itype.value, 
                                            'Summary': title,                                           
                                            'Notes': source,
                                            'Description' : body})), 
                self.jira)

    def get_issues(self) -> List[jr.Issue]:
        return list(self.jira.search_issues(f"project = {self.project} AND resolution = Unresolved ORDER BY priority DESC, updated DESC"))


    def get_issue(self, key) -> jr.Issue:
        return self.jira.issue(key, fields=','.join(self.field_name_to_id[key] for key in ('Summary', 'Notes', 'Description')))

def main():
    pass


if __name__ == '__main__':
    jira = JiraConn('MZDASH')
    gh_issues_exists = set()
    for ji in jira.get_issues():
        if '[GHI #' in ji.fields.summary:
            github_link = ji.get_field(jira.field_name_to_id['Notes'])
            gh_issues_exists.add(github_link)
    
    g = Github("")
    repo = g.get_repo("intel-sandbox/applications.ai.modelzoo.dashboard")
    open_issues = repo.get_issues(state='open')
    skiped = 0
    synced = 0
    for issue in open_issues:
        labels = [l.name.lower() for l in issue.labels]
        if issue.url in gh_issues_exists:
            print(f'issue #{issue.number} already synced')
            skiped += 1
            continue

        is_bug = 'fix' in issue.title.lower() or 'bug' in labels
        print(f'issue #{issue.number}: {issue.title} @{issue.url} {"is" if is_bug else "is not"} a bug' )
        print("Body:\n=========")
        print(issue.body)
        
        if False:
            jissue = jira.create_issue(JiraIssueType.Bug if is_bug else JiraIssueType.Epic,
                title=f'[GHI #{issue.number}] {issue.title}',
                body = f'from: {issue.url}\n\n{issue.body}',
                source= issue.url
            )        

            print("Comments:\n=========")
            for c in issue.get_comments():
                print("\t", c.user.login+":", c.body)            
                jissue.add_comment('from: '+c.user.login + ':\n' + c.body)
            print('--------------------------------------------------------------')
        synced += 1

    print(synced, "issues synced")
    print(skiped, "issues skiped")
