CREATE_ISSUE_MUTATION = """
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      title
      description
      priority
      url
      createdAt
      updatedAt
      assignee { id name }
      team { id name }
      project { id name }
      state { id name }
    }
  }
}
"""

UPDATE_ISSUE_MUTATION = """
mutation UpdateIssue($input: IssueUpdateInput!) {
  issueUpdate(input: $input) {
    success
    issue {
      id
      title
      description
      priority
      url
      createdAt
      updatedAt
      assignee { id name }
      team { id name }
      project { id name }
      state { id name }
    }
  }
}
"""

DELETE_ISSUE_MUTATION = """
mutation DeleteIssue($input: IssueDeleteInput!) {
  issueDelete(input: $input) {
    success
  }
}
"""

CHECK_ISSUE_EXISTS_QUERY = """
query Issue($issueId: String!) {
  issue(id: $issueId) {
    id
  }
}
"""