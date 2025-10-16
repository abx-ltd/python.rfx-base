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
mutation UpdateIssue($issueId: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $issueId, input: $input) {
    success
    issue {
      id
      identifier
      title
      updatedAt
      state {
        name
      }
      assignee {
        name
      }
    }
  }
}
"""

DELETE_ISSUE_MUTATION = """
mutation IssueDelete($issueDeleteId: String!, $permanentlyDelete: Boolean) {
  issueDelete(id: $issueDeleteId, permanentlyDelete: $permanentlyDelete) {
    entity {
      id
      url
    }
    success
    lastSyncId
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