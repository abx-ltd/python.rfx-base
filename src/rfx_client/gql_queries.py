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
mutation UpdateDetailedProject($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
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

DELETE_PROJECT_MUTATION = """
mutation DeleteProject($projectDeleteId: String!) {
  projectDelete(id: $projectDeleteId) {
    success
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




# milestone 

CREATE_PROJECT_MILESTONE_MUTATION = """
mutation ProjectMilestoneCreate($input: ProjectMilestoneCreateInput!) {
  projectMilestoneCreate(input: $input) {
    lastSyncId
    projectMilestone {
      id
      name
      description
      createdAt
      progress
      status
      sortOrder
      targetDate
      updatedAt
    }
    success
  }
}
"""

UPDATE_PROJECT_MILESTONE_MUTATION = """
mutation ProjectMilestoneUpdate($projectMilestoneUpdateId: String!, $input: ProjectMilestoneUpdateInput!) {
  projectMilestoneUpdate(id: $projectMilestoneUpdateId, input: $input) {
    lastSyncId
    projectMilestone {
      id
      name
      description
    }
    success
  }
}
"""

DELETE_PROJECT_MILESTONE_MUTATION = """
mutation ProjectDelete($projectDeleteId: String!) {
  projectDelete(id: $projectDeleteId) {
    entity {
      url
      id
    }
    lastSyncId
    success
  }
}
"""


CHECK_PROJECT_MILESTONE_EXISTS_QUERY = """
query ProjectMilestone($projectMilestoneId: String!) {
  projectMilestone(id: $projectMilestoneId) {
    id
    name
    description
    progress
    status
    updatedAt
    targetDate
  }
}
"""

