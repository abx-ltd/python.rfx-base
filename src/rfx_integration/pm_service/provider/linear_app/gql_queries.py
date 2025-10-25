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
      url
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


CREATE_PROJECT_MUTATION = """
mutation CreateDetailedProject($input: ProjectCreateInput!) {
  projectCreate(input: $input) {
    success
    project {
      id
      name
      description
      color
      icon
      status { name id }
      priorityLabel
      url
      lead { id name email }
      members { nodes { id name } }
      labels { nodes { id name } }
      teams { nodes { id name } }
      startDate
      targetDate
      createdAt
      updatedAt
    }
    lastSyncId
  }
}
"""

UPDATE_PROJECT_MUTATION = """
mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project {
      id
      name
      description
      url
      state
      updatedAt
      lead {
        id
        name
      }
      startDate
      targetDate
      color
      icon
    }
  }
}
"""

DELETE_PROJECT_MUTATION = """
mutation DeleteProject($projectId: String!) {
  projectDelete(id: $projectId) {
    success
  }
}
"""
ARCHIVE_PROJECT_MUTATION = """
mutation ArchiveProject($id: String!) {
  projectArchive(id: $id) {
    success
    project {
      id
      archivedAt
    }
  }
}
"""

CHECK_PROJECT_EXISTS_QUERY = """
query Project($projectId: String!) {
  project(id: $projectId) {
        id
  }
}
"""

GET_PROJECTS_QUERY_URL = """
query Project($projectId: String!) {
  project(id: $projectId) {
    url
  }
}
"""




# ========== PROJECT MILESTONE MUTATIONS ==========

CREATE_PROJECT_MILESTONE_MUTATION = """
mutation CreateProjectMilestone($input: ProjectMilestoneCreateInput!) {
  projectMilestoneCreate(input: $input) {
    success
    projectMilestone {
      id
      name
      description
      targetDate
      sortOrder
      createdAt
      updatedAt
      project {
        id
        name
        url
      }
    }
  }
}
"""

UPDATE_PROJECT_MILESTONE_MUTATION = """
mutation UpdateProjectMilestone($id: String!, $input: ProjectMilestoneUpdateInput!) {
  projectMilestoneUpdate(id: $id, input: $input) {
    success
    projectMilestone {
      id
      name
      description
      targetDate
      sortOrder
      updatedAt
      project {
        id
        name
        url
      }
    }
  }
}
"""

DELETE_PROJECT_MILESTONE_MUTATION = """
mutation DeleteProjectMilestone($id: String!) {
  projectMilestoneDelete(id: $id) {
    success
  }
}
"""

# ========== PROJECT MILESTONE QUERIES ==========

GET_PROJECT_MILESTONE_QUERY = """
query GetProjectMilestone($id: String!) {
  projectMilestone(id: $id) {
    id
    name
    description
    targetDate
    sortOrder
    createdAt
    updatedAt
    project {
      id
      name
      url
    }
  }
}
"""

LIST_PROJECT_MILESTONES_QUERY = """
query ListProjectMilestones($projectId: String!) {
  project(id: $projectId) {
    id
    name
    projectMilestones {
      nodes {
        id
        name
        description
        targetDate
        sortOrder
        createdAt
        updatedAt
      }
    }
  }
}
"""


# ========== PROJECT UPDATE MUTATIONS ==========

CREATE_PROJECT_UPDATE_MUTATION = """
mutation CreateProjectUpdate($input: ProjectUpdateCreateInput!) {
  projectUpdateCreate(input: $input) {
    success
    projectUpdate {
      id
      body
      health
      project {
        id
        name
        url
      }
      createdAt
      updatedAt
    }
  }
}
"""

GET_PROJECT_UPDATE_QUERY = """
query GetProjectUpdate($id: String!) {
  projectUpdate(id: $id) {
    id
    body
    health
    project {
      id
      name
    }
  }
}
"""

LIST_PROJECT_UPDATES_QUERY = """
query ListProjectUpdates($projectId: String!) {
  project(id: $projectId) {
    id
    name
    projectUpdates(first: 50) {
      nodes {
        id
        body
        health
        createdAt
      }
    }
  }
}
"""
