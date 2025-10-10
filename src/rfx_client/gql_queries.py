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

