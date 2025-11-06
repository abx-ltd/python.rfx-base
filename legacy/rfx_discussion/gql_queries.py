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



#---------- Query Commmnet to Linear ----------

CREATE_ISSUE_MUTATION_COMMENT = """
mutation CommentCreate($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    comment {
      body
      bodyData
      documentContentId
      editedAt
      id
      issue {
        id
        identifier
        title
        url
      }
      parent {
        id
        body
        bodyData
      }
      post {
        id
        body
        bodyData
        title
      }
      resolvedAt
      updatedAt
      url
    }
  }
}
"""

UPDATE_ISSUE_MUTATION_COMMENT = """
mutation CommentUpdate($commentUpdateId: String!, $input: CommentUpdateInput!) {
  commentUpdate(id: $commentUpdateId, input: $input) {
    comment {
      body
      bodyData
      id
      url
    }
    lastSyncId
    success
  }
}
"""

DELETE_ISSUE_MUTATION_COMMENT = """
mutation CommentDelete($commentDeleteId: String!) {
  commentDelete(id: $commentDeleteId) {
    entityId
    lastSyncId
    success
  }
}
"""


CHECK_COMMENT_EXISTS_QUERY = """
query GetComment($id: String!) {
  comment(id: $id) {
    id
    url
  }
}
"""
